from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Booking, Agent, Bid, Transaction
from app.schemas.auction import BookingResponse

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

class SplitAction(BaseModel):
    agent_id: str

@router.post("/{booking_id}/split/accept", response_model=BookingResponse)
async def accept_split(booking_id: str, action: SplitAction, db: AsyncSession = Depends(get_db)):
    # 1. Get booking
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # 2. Verify split
    if booking.split_with_agent_id != action.agent_id:
        raise HTTPException(status_code=403, detail="Not the designated split partner")
    if booking.split_status != "pending":
        raise HTTPException(status_code=400, detail=f"Split status is {booking.split_status}")

    # 3. Get agents and bid
    agent_result = await db.execute(select(Agent).where(Agent.id == action.agent_id))
    partner = agent_result.scalar_one_or_none()
    
    owner_result = await db.execute(select(Agent).where(Agent.id == booking.agent_id))
    owner = owner_result.scalar_one_or_none()
    
    bid_result = await db.execute(select(Bid).where(Bid.id == booking.bid_id))
    bid = bid_result.scalar_one_or_none()
    
    if not partner or not owner or not bid:
        raise HTTPException(status_code=404, detail="Related entities not found")

    # 4. Calculate split amount (50%)
    split_amount = bid.amount / 2.0
    
    if partner.token_balance < split_amount:
        raise HTTPException(status_code=400, detail="Insufficient funds to accept split")

    # 5. Transfer tokens: Partner -> Owner
    partner.token_balance -= split_amount
    owner.token_balance += split_amount
    
    # Record transactions
    tx_p = Transaction(
        agent_id=partner.id,
        amount=-split_amount,
        type="split_payment",
        reference_id=booking.id
    )
    tx_o = Transaction(
        agent_id=owner.id,
        amount=split_amount,
        type="split_reimbursement",
        reference_id=booking.id
    )
    db.add(tx_p)
    db.add(tx_o)
    
    # 6. Update booking
    booking.split_status = "accepted"
    
    await db.commit()
    await db.refresh(booking)
    return booking

    booking.split_status = "rejected"
    await db.commit()
    await db.refresh(booking)
    return booking

class SellBackAction(BaseModel):
    agent_id: str

@router.post("/{booking_id}/sell-back")
async def sell_back_booking(booking_id: str, action: SellBackAction, db: AsyncSession = Depends(get_db)):
    """Sell a booking back to the market for 80% refund."""
    from app.models import TimeSlot, TimeSlotStatus, Auction, AuctionStatus

    # 1. Get booking
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.agent_id != action.agent_id:
        raise HTTPException(status_code=403, detail="Not the booking owner")
        
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    # 2. Calculate Refund
    refund_amount = round(booking.price * 0.8, 2)
    
    # 3. Refund Agent
    agent_res = await db.execute(select(Agent).where(Agent.id == action.agent_id))
    agent = agent_res.scalar_one_or_none()
    if agent:
        agent.token_balance += refund_amount
        
        # 4. Record Transaction
        tx = Transaction(
            agent_id=agent.id,
            amount=refund_amount,
            type="sell_back_refund",
            reference_id=booking.id
        )
        db.add(tx)
    
    # 5. Reset Slot & Auction
    # We need to find the slot
    slot_res = await db.execute(select(TimeSlot).where(TimeSlot.id == booking.time_slot_id))
    slot = slot_res.scalar_one_or_none()
    if slot:
        slot.status = TimeSlotStatus.IN_AUCTION
        
        # Reset Auction if exists
        auc_res = await db.execute(select(Auction).where(Auction.time_slot_id == slot.id))
        auction = auc_res.scalar_one_or_none()
        if auction:
             auction.status = AuctionStatus.ACTIVE
             # Optional: Reset price to what it was? Or keep it at clearing price?
             # Let's keep it current to avoid arbitrage, or maybe bump it up?
             # For now, just make it active.
    
    # 6. Update Booking
    booking.status = "cancelled"
    
    await db.commit()
    return {"message": "Booking sold back", "refund_amount": refund_amount}
