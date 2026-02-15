from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Agent,
    Auction,
    Bid,
    Booking,
    GroupBidMember,
    TimeSlot,
    TimeSlotStatus,
    Resource,
)


async def create_booking_from_bid(
    auction: Auction, bid: Bid, db: AsyncSession
) -> list[Booking]:
    """Create bookings for the winning bid. For group bids, all members get a booking."""
    slot_result = await db.execute(select(TimeSlot).where(TimeSlot.id == auction.time_slot_id))
    slot = slot_result.scalar_one()

    resource_result = await db.execute(select(Resource).where(Resource.id == slot.resource_id))
    resource = resource_result.scalar_one()

    # Check room capacity
    existing_count_result = await db.execute(
        select(func.count()).select_from(Booking).where(Booking.time_slot_id == slot.id)
    )
    existing_count = existing_count_result.scalar()

    if bid.is_group_bid:
        # Get group members
        members_result = await db.execute(
            select(GroupBidMember).where(GroupBidMember.bid_id == bid.id)
        )
        members = members_result.scalars().all()
        agent_ids = [m.agent_id for m in members]
    else:
        agent_ids = [bid.agent_id]

    # Check capacity
    if existing_count + len(agent_ids) > resource.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Room capacity ({resource.capacity}) would be exceeded",
        )

    bookings = []
    for agent_id in agent_ids:
        # Check agent hasn't already booked this time slot
        dup_result = await db.execute(
            select(Booking).where(
                Booking.agent_id == agent_id,
                Booking.time_slot_id == slot.id,
            )
        )
        if dup_result.scalar_one_or_none():
            continue  # Skip duplicate

        # Check agent doesn't have another room at same time
        overlap_result = await db.execute(
            select(Booking)
            .join(TimeSlot)
            .where(
                Booking.agent_id == agent_id,
                TimeSlot.start_time == slot.start_time,
                TimeSlot.id != slot.id,
            )
        )
        if overlap_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} already has a booking at this time",
            )

        # Check max bookings
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one()
        booking_count_result = await db.execute(
            select(func.count()).select_from(Booking).where(Booking.agent_id == agent_id)
        )
        booking_count = booking_count_result.scalar()
        if booking_count >= agent.max_bookings:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} has reached max bookings ({agent.max_bookings})",
            )

        booking = Booking(
            time_slot_id=slot.id,
            agent_id=agent_id,
            bid_id=bid.id,
            split_with_agent_id=bid.split_with_agent_id if not bid.is_group_bid else None,
            split_status="pending" if bid.split_with_agent_id else "none",
        )
        db.add(booking)
        bookings.append(booking)

    # Mark slot as booked only when at full capacity
    if bookings:
        total_bookings_result = await db.execute(
            select(func.count()).select_from(Booking).where(Booking.time_slot_id == slot.id)
        )
        total_bookings = total_bookings_result.scalar()
        if total_bookings >= resource.capacity:
            slot.status = TimeSlotStatus.BOOKED

    return bookings
