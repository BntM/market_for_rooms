from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AdminConfig,
    Agent,
    Auction,
    AuctionStatus,
    Bid,
    BidStatus,
    GroupBidMember,
    LimitOrder,
    LimitOrderStatus,
    PriceHistory,
    TimeSlot,
    TimeSlotStatus,
)
from app.schemas.auction import (
    AuctionCreate,
    AuctionResponse,
    BidCreate,
    BidResponse,
    LimitOrderCreate,
    LimitOrderResponse,
    PriceHistoryResponse,
)
from app.services.auction_engine import get_auction_engine
from app.services.booking_service import create_booking_from_bid

router = APIRouter(prefix="/api/auctions", tags=["auctions"])


@router.post("/", response_model=AuctionResponse, status_code=201)
async def create_auction(data: AuctionCreate, db: AsyncSession = Depends(get_db)):
    # Verify time slot exists and is available
    result = await db.execute(select(TimeSlot).where(TimeSlot.id == data.time_slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    if slot.status != TimeSlotStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Time slot is not available")

    # Get defaults from admin config
    cfg_result = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = cfg_result.scalar_one_or_none()

    auction = Auction(
        time_slot_id=data.time_slot_id,
        auction_type=data.auction_type,
        start_price=data.start_price or (config.dutch_start_price if config else 100.0),
        current_price=data.start_price or (config.dutch_start_price if config else 100.0),
        min_price=data.min_price or (config.dutch_min_price if config else 10.0),
        price_step=data.price_step or (config.dutch_price_step if config else 5.0),
        tick_interval_sec=data.tick_interval_sec or (config.dutch_tick_interval_sec if config else 10.0),
    )
    db.add(auction)

    slot.status = TimeSlotStatus.IN_AUCTION
    await db.commit()
    await db.refresh(auction)
    return auction


@router.get("/", response_model=list[AuctionResponse])
async def list_auctions(
    status: str | None = None,
    resource_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Auction)
    if status:
        query = query.where(Auction.status == status)
    if resource_id:
        query = query.join(TimeSlot).where(TimeSlot.resource_id == resource_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(auction_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


@router.post("/{auction_id}/start", response_model=AuctionResponse)
async def start_auction(auction_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Auction is not in pending state")

    engine = get_auction_engine(auction.auction_type)
    await engine.start(auction, db)
    await db.commit()
    await db.refresh(auction)
    return auction


@router.post("/{auction_id}/tick", response_model=AuctionResponse)
async def tick_auction(auction_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")

    engine = get_auction_engine(auction.auction_type)
    await engine.tick(auction, db)
    await db.commit()
    await db.refresh(auction)
    return auction


@router.post("/{auction_id}/bid", response_model=BidResponse)
async def place_bid(
    auction_id: str,
    data: BidCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")

    engine = get_auction_engine(auction.auction_type)
    bid = await engine.place_bid(auction, data, db)
    await db.commit()
    await db.refresh(bid)

    # If bid was accepted, create booking
    if bid.status == BidStatus.ACCEPTED:
        await create_booking_from_bid(auction, bid, db)
        await db.commit()

    return bid


@router.get("/{auction_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(auction_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.auction_id == auction_id)
        .order_by(PriceHistory.recorded_at)
    )
    return result.scalars().all()


@router.post("/{auction_id}/limit-order", response_model=LimitOrderResponse, status_code=201)
async def create_limit_order(
    auction_id: str,
    data: LimitOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")

    agent_result = await db.execute(select(Agent).where(Agent.id == data.agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.token_balance < data.max_price:
        raise HTTPException(status_code=400, detail="Insufficient token balance for limit order")

    order = LimitOrder(
        agent_id=data.agent_id,
        time_slot_id=auction.time_slot_id,
        max_price=data.max_price,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.delete("/limit-orders/{order_id}", status_code=204)
async def cancel_limit_order(order_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LimitOrder).where(LimitOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Limit order not found")
    if order.status != LimitOrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")

    order.status = LimitOrderStatus.CANCELLED
    await db.commit()
    return None
