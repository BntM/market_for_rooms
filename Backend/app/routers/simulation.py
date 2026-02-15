from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    AdminConfig,
    Agent,
    AgentPreference,
    Auction,
    AuctionStatus,
    Bid,
    Booking,
    GroupBidMember,
    PriceHistory,
    TimeSlot,
    TimeSlotStatus,
    Transaction,
)
from app.models.limit_order import LimitOrder
from app.schemas.agent import AgentResponse, BulkAgentCreate
from app.services.auction_engine import get_auction_engine
from app.services.preference_generator import generate_preferences_for_agent
from app.services.pricing_service import recalculate_prices
from app.services.simulation_service import (
    get_simulation_results,
    run_simulation_round,
    simulate_semester,
    trigger_agent_actions,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

@router.post("/time/advance-day")
async def advance_day(db: AsyncSession = Depends(get_db)):
    import traceback
    try:
        """Advance simulation time by 24 hours."""
        # 1. Update Config Date
        res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
        config = res.scalar_one_or_none()
        if not config:
            config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 15, 9, 0))
            db.add(config)
        elif config.current_simulation_date is None:
            config.current_simulation_date = datetime(2026, 2, 15, 9, 0)
        
        # Advance in steps if we want granular behavior, or just jump
        # For interactive simulation, we usually want to jump but trigger logic
        # Let's jump 1 day but trigger actions for "today"
        
        current_date = config.current_simulation_date
        config.current_simulation_date += timedelta(days=1)
        
        # 2. Recalculate Prices
        await recalculate_prices(db, config.current_simulation_date)
        
        # 3. Trigger Agent Actions (Simulate activity for the day passed)
        # We might want to simulate hour by hour, but for speed just trigger once?
        # Better: Simulate a few key hours (9, 12, 15) to get spread
        actions = 0
        for h in [9, 12, 15, 18]:
            sim_time = current_date.replace(hour=h, minute=0)
            actions += await trigger_agent_actions(db, sim_time)
        
        await db.commit()
        return {"current_date": config.current_simulation_date.isoformat(), "message": "Advanced 1 day", "actions_triggered": actions}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/time/advance-hour")
async def advance_hour(db: AsyncSession = Depends(get_db)):
    """Advance simulation time by 1 hour."""
    # 1. Update Config Date
    res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = res.scalar_one_or_none()
    if not config:
        config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 15, 9, 0))
        db.add(config)
    elif config.current_simulation_date is None:
        config.current_simulation_date = datetime(2026, 2, 15, 9, 0)
    
    current_date = config.current_simulation_date
    config.current_simulation_date += timedelta(hours=1)
    new_date = config.current_simulation_date
    
    # 2. Recalculate Prices (Dynamic Pricing reaction)
    await recalculate_prices(db, new_date)
    
    # 3. Agent Actions
    actions = await trigger_agent_actions(db, current_date) # Act on the hour that just finished/ongoing
    
    await db.commit()
    return {"current_date": new_date.isoformat(), "message": "Advanced 1 hour", "actions_triggered": actions}

@router.post("/time/reset")
async def reset_time(db: AsyncSession = Depends(get_db)):
    """Reset simulation time to Feb 15."""
    res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = res.scalar_one_or_none()
    if config:
        config.current_simulation_date = datetime(2026, 2, 15, 9, 0)
    else:
        config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 15, 9, 0))
        db.add(config)
    
    await db.commit()
    return {"current_date": "2026-02-15T09:00:00", "message": "Time reset"}


@router.post("/reset")
async def reset_simulation(db: AsyncSession = Depends(get_db)):
    """Reset all simulation data (auctions, bookings, etc.).
    Preserves resources, time slots, admin config, and agents (with reset balances)."""
    # Get admin config for default balance
    config_result = await db.execute(select(AdminConfig))
    config = config_result.scalar_one_or_none()
    default_balance = config.token_starting_amount if config else 100.0
    
    # Reset Date as well
    if config:
        config.current_simulation_date = datetime(2026, 2, 15, 9, 0)

    # Delete in dependency order
    await db.execute(delete(GroupBidMember))
    await db.execute(delete(LimitOrder))
    await db.execute(delete(Booking))
    await db.execute(delete(PriceHistory))
    await db.execute(delete(Transaction))
    await db.execute(delete(Bid))
    await db.execute(delete(Auction))
    await db.execute(delete(AgentPreference))

    # Reset agents instead of deleting them
    agent_result = await db.execute(select(Agent))
    agents = agent_result.scalars().all()
    if agents:
        for agent in agents:
            agent.token_balance = default_balance
    else:
        # No agents exist — seed defaults
        for i in range(1, 7):
            db.add(Agent(name=f"User_{i}", token_balance=default_balance, max_bookings=10))

    # Reset time slot statuses and recreate auctions
    result = await db.execute(select(TimeSlot))
    slots = result.scalars().all()

    start_price = config.dutch_start_price if config else 80.0
    min_price = config.dutch_min_price if config else 5.0
    price_step = config.dutch_price_step if config else 3.0
    tick_interval = config.dutch_tick_interval_sec if config else 10.0

    auctions_to_insert = []
    created_at = config.current_simulation_date if config else datetime.utcnow()
    
    # Bulk Update Slots status? Ideally, but iterating objects updates session
    # For speed, we might want bulk update too, but object iteration is okay for now if we bulk insert auctions
    
    for slot in slots:
        slot.status = TimeSlotStatus.IN_AUCTION
        auctions_to_insert.append({
            "id": str(uuid.uuid4()), # We need to import uuid if not present, check
            "time_slot_id": slot.id,
            "auction_type": "dutch",
            "start_price": start_price,
            "current_price": start_price,
            "min_price": min_price,
            "price_step": price_step,
            "tick_interval_sec": tick_interval,
            "created_at": created_at,
            "status": AuctionStatus.ACTIVE
        })
    
    if auctions_to_insert:
        from sqlalchemy import insert
        await db.execute(insert(Auction), auctions_to_insert)
        
    # We need to start engines? 
    # get_auction_engine("dutch").start() usually just sets status to active or logs
    # If engine.start does DB changes, we might skip it or do it in bulk. 
    # Standard Dutch auction start just is "Active".
     

    await db.commit()
    return {"status": "reset_complete"}
