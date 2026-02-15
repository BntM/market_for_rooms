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

async def simulate_semester(db: AsyncSession, weeks: int = 1):
    """Simulate agent behavior over time."""
    import random
    import uuid
    from datetime import timedelta
    from app.services.pricing_service import recalculate_prices
    
    # 1. Get Agents
    agents_res = await db.execute(select(Agent).where(Agent.is_simulated == True))
    agents = agents_res.scalars().all()
    if not agents:
        return {"message": "No simulated agents found"}

    # 2. Get Config for current date
    config_res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = config_res.scalar_one_or_none()
    current_date = config.current_simulation_date
    
    start_date = current_date
    total_actions = 0
    days_to_sim = weeks * 7
    
    for day in range(days_to_sim):
        # A. Advance Day
        current_date += timedelta(days=1)
        config.current_simulation_date = current_date
        
        # B. Recalc Prices (Morning update)
        await recalculate_prices(db, current_date, days=7)
        
        # C. Agent Actions
        # Each agent considers booking something in the next 7 days
        future_window = current_date + timedelta(days=7)
        
        # Optimize: Fetch available slots once per day to avoid DB spam
        slots_res = await db.execute(
            select(TimeSlot, Auction)
            .outerjoin(Auction, Auction.time_slot_id == TimeSlot.id)
            .where(
                TimeSlot.start_time >= current_date,
                TimeSlot.start_time <= future_window,
                TimeSlot.status == TimeSlotStatus.AVAILABLE
            )
        )
        available_slots = slots_res.all() # [(TimeSlot, Auction), ...]
        
        if not available_slots:
            continue
            
        for agent in agents:
            # 1. Check constraints
            # (Simplified check, assumes booking count is low enough)
            
            # 2. Filter by preference
            # preferred_days string "0,2,4"
            pref_days = [int(d) for d in agent.behavior_preferred_days.split(",") if d.strip().isdigit()]
            
            candidates = []
            for slot, auction in available_slots:
                if slot.start_time.weekday() in pref_days:
                    candidates.append((slot, auction))
            
            if not candidates: continue
            
            # 3. Decision (Pick one random candidate for now, biased by flexibility)
            # If flexible, maybe look at others? For now stick to pref.
            
            target_slot, target_auction = random.choice(candidates)
            if not target_auction: continue
            
            # 4. Price Check
            price = target_auction.current_price
            # Sensitivity 0 (Rich) to 1 (Cheap). 
            # Willingness to pay = Base * (1 - sensitivity * 0.5)
            # Just a mock formula:
            willingness = 200.0 * (1.0 - (agent.behavior_price_sensitivity * 0.8))
            
            if price <= willingness:
                # BUY IT
                # direct buy logic (inline for speed)
                # In real app, call booking service. Here we hack it for simulation speed.
                
                target_auction.status = AuctionStatus.COMPLETED
                target_auction.final_price = price
                target_slot.status = TimeSlotStatus.BOOKED
                
                # Record booking
                # (Skipping full booking record creation for pure speed if just showing occupancy? 
                #  No, let's create booking to show up in User dashboard)
                from app.models import Booking
                new_booking = Booking(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    time_slot_id=target_slot.id,
                    price=price,
                    status="confirmed",
                    booked_at=current_date
                )
                db.add(new_booking)
                total_actions += 1
                
                # Remove from available for next agent
                available_slots.remove((target_slot, target_auction))

    await db.commit()
    return {"days_simulated": days_to_sim, "bookings_made": total_actions}
