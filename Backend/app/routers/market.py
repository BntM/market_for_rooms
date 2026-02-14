from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Auction,
    AuctionStatus,
    Booking,
    PriceHistory,
    Resource,
    TimeSlot,
    TimeSlotStatus,
)
from app.schemas.auction import AuctionResponse, BookingResponse, PriceHistoryResponse
from app.schemas.resource import ResourceResponse, TimeSlotResponse

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/state")
async def get_market_state(db: AsyncSession = Depends(get_db)):
    # Active auctions
    active_result = await db.execute(
        select(Auction).where(Auction.status == AuctionStatus.ACTIVE)
    )
    active_auctions = active_result.scalars().all()

    # Counts
    total_resources = await db.execute(select(func.count()).select_from(Resource))
    available_slots = await db.execute(
        select(func.count())
        .select_from(TimeSlot)
        .where(TimeSlot.status == TimeSlotStatus.AVAILABLE)
    )
    total_bookings = await db.execute(select(func.count()).select_from(Booking))

    return {
        "active_auctions": [AuctionResponse.model_validate(a) for a in active_auctions],
        "total_resources": total_resources.scalar(),
        "available_slots": available_slots.scalar(),
        "total_bookings": total_bookings.scalar(),
    }


@router.get("/price-history", response_model=list[PriceHistoryResponse])
async def get_all_price_history(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PriceHistory)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/resources", response_model=list[ResourceResponse])
async def get_resources_with_availability(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resource).where(Resource.is_active == True))
    return result.scalars().all()


@router.get("/resources/{resource_id}/schedule")
async def get_resource_schedule(resource_id: str, db: AsyncSession = Depends(get_db)):
    slots_result = await db.execute(
        select(TimeSlot)
        .where(TimeSlot.resource_id == resource_id)
        .order_by(TimeSlot.start_time)
    )
    slots = slots_result.scalars().all()

    schedule = []
    for slot in slots:
        bookings_result = await db.execute(
            select(Booking).where(Booking.time_slot_id == slot.id)
        )
        bookings = bookings_result.scalars().all()
        schedule.append({
            "slot": TimeSlotResponse.model_validate(slot),
            "bookings": [BookingResponse.model_validate(b) for b in bookings],
        })
    return schedule
