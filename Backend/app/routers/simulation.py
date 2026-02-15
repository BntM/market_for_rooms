from datetime import datetime, timedelta

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
)
from app.services.token_service import allocate_tokens

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/simulate-semester")
async def trigger_simulate_semester(weeks: int = 1, db: AsyncSession = Depends(get_db)):
    """Run a semester simulation (behavior-based)."""
    return await simulate_semester(db, weeks=weeks)


@router.post("/agents/generate", response_model=list[AgentResponse], status_code=201)
async def generate_agents(data: BulkAgentCreate, db: AsyncSession = Depends(get_db)):
    """Generate agents with preferences drawn from admin popularity distributions."""
    agents = []
    for i in range(data.count):
        agent = Agent(
            name=f"{data.name_prefix}_{i + 1}",
            token_balance=data.initial_balance,
            max_bookings=data.max_bookings,
        )
        db.add(agent)
        agents.append(agent)

    await db.flush()

    if data.generate_preferences:
        for agent in agents:
            await generate_preferences_for_agent(agent, db)

    await db.commit()
    for agent in agents:
        await db.refresh(agent)
    return agents


@router.post("/round")
async def run_round(db: AsyncSession = Depends(get_db)):
    """Run one simulation round (allocate tokens, tick auctions)."""
    result = await run_simulation_round(db)
    return result


@router.post("/allocate-tokens")
async def trigger_token_allocation(db: AsyncSession = Depends(get_db)):
    """Manually trigger token allocation to all active agents."""
    transactions = await allocate_tokens(db)
    await db.commit()
    return {"tokens_allocated": len(transactions)}


@router.get("/results")
async def get_results(db: AsyncSession = Depends(get_db)):
    """Get simulation metrics."""
    return await get_simulation_results(db)


@router.post("/time/advance-day")
async def advance_day(db: AsyncSession = Depends(get_db)):
    """Advance simulation time by 24 hours."""
    # 1. Update Config Date
    res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = res.scalar_one_or_none()
    if not config:
        config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 14, 9, 0))
        db.add(config)
    elif config.current_simulation_date is None:
        config.current_simulation_date = datetime(2026, 2, 14, 9, 0)
    
    config.current_simulation_date += timedelta(days=1)
    new_date = config.current_simulation_date
    
    # 2. Recalculate Prices
    await recalculate_prices(db, new_date)
    
    await db.commit()
    return {"current_date": new_date.isoformat(), "message": "Advanced 1 day"}

@router.post("/time/advance-hour")
async def advance_hour(db: AsyncSession = Depends(get_db)):
    """Advance simulation time by 1 hour."""
    # 1. Update Config Date
    res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = res.scalar_one_or_none()
    if not config:
        config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 14, 9, 0))
        db.add(config)
    elif config.current_simulation_date is None:
        config.current_simulation_date = datetime(2026, 2, 14, 9, 0)
    
    config.current_simulation_date += timedelta(hours=1)
    new_date = config.current_simulation_date
    
    # 2. Recalculate Prices (Dynamic Pricing reaction)
    await recalculate_prices(db, new_date)
    
    await db.commit()
    return {"current_date": new_date.isoformat(), "message": "Advanced 1 hour"}

@router.post("/time/reset")
async def reset_time(db: AsyncSession = Depends(get_db)):
    """Reset simulation time to Feb 14."""
    res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = res.scalar_one_or_none()
    if config:
        config.current_simulation_date = datetime(2026, 2, 14, 9, 0)
    else:
        config = AdminConfig(id=1, current_simulation_date=datetime(2026, 2, 14, 9, 0))
        db.add(config)
    
    await db.commit()
    return {"current_date": "2026-02-14T09:00:00", "message": "Time reset"}


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
        config.current_simulation_date = datetime(2026, 2, 14, 9, 0)

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

    engine = get_auction_engine("dutch")
    for slot in slots:
        slot.status = TimeSlotStatus.IN_AUCTION
        auction = Auction(
            time_slot_id=slot.id,
            auction_type="dutch",
            start_price=start_price,
            current_price=start_price,
            min_price=min_price,
            price_step=price_step,
            tick_interval_sec=tick_interval,
            created_at=config.current_simulation_date if config else datetime.utcnow()
        )
        db.add(auction)
        await db.flush()
        await engine.start(auction, db)

    await db.commit()
    return {"status": "reset_complete"}
