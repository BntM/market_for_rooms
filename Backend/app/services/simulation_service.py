from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AdminConfig,
    Agent,
    Auction,
    AuctionStatus,
    Booking,
    PriceHistory,
    TimeSlot,
    TimeSlotStatus,
)
from app.services.auction_engine import get_auction_engine
from app.services.token_service import allocate_tokens


async def run_simulation_round(db: AsyncSession) -> dict:
    """Run one complete simulation round:
    1. Allocate tokens to all agents
    2. Tick all active auctions
    3. Return round summary
    """
    # Step 1: Allocate tokens
    transactions = await allocate_tokens(db)

    # Step 2: Tick all active auctions
    active_result = await db.execute(
        select(Auction).where(Auction.status == AuctionStatus.ACTIVE)
    )
    active_auctions = active_result.scalars().all()

    ticked = 0
    for auction in active_auctions:
        engine = get_auction_engine(auction.auction_type)
        await engine.tick(auction, db)
        ticked += 1

    await db.commit()

    # Step 3: Gather summary
    total_agents = await db.execute(
        select(func.count()).select_from(Agent).where(Agent.is_active == True)
    )
    total_bookings = await db.execute(select(func.count()).select_from(Booking))
    avg_price_result = await db.execute(select(func.avg(PriceHistory.price)))

    return {
        "tokens_allocated": len(transactions),
        "auctions_ticked": ticked,
        "total_active_agents": total_agents.scalar(),
        "total_bookings": total_bookings.scalar(),
        "average_price": round(avg_price_result.scalar() or 0, 2),
    }


async def get_simulation_results(db: AsyncSession) -> dict:
    """Get comprehensive simulation metrics."""
    # Clearing prices (completed auctions)
    completed_result = await db.execute(
        select(Auction).where(Auction.status == AuctionStatus.COMPLETED)
    )
    completed = completed_result.scalars().all()
    clearing_prices = [a.current_price for a in completed]

    # Utilization
    total_slots = await db.execute(select(func.count()).select_from(TimeSlot))
    booked_slots = await db.execute(
        select(func.count())
        .select_from(TimeSlot)
        .where(TimeSlot.status == TimeSlotStatus.BOOKED)
    )
    total = total_slots.scalar()
    booked = booked_slots.scalar()

    # Token velocity
    from app.models import Transaction

    total_volume = await db.execute(
        select(func.sum(func.abs(Transaction.amount)))
        .where(Transaction.type == "bid_payment")
    )

    return {
        "completed_auctions": len(completed),
        "clearing_prices": clearing_prices,
        "avg_clearing_price": round(sum(clearing_prices) / len(clearing_prices), 2) if clearing_prices else 0,
        "utilization": round(booked / total, 4) if total else 0,
        "total_slots": total,
        "booked_slots": booked,
        "token_volume": round(total_volume.scalar() or 0, 2),
    }
