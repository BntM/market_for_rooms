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
from app.schemas.agent import AgentResponse, BulkAgentCreate
from app.services.preference_generator import generate_preferences_for_agent
from app.services.simulation_service import get_simulation_results, run_simulation_round
from app.services.token_service import allocate_tokens

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


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


@router.post("/reset")
async def reset_simulation(db: AsyncSession = Depends(get_db)):
    """Reset all simulation data (agents, auctions, bookings, etc.).
    Preserves resources, time slots, and admin config."""
    # Delete in dependency order
    await db.execute(delete(GroupBidMember))
    await db.execute(delete(Booking))
    await db.execute(delete(PriceHistory))
    await db.execute(delete(Transaction))
    await db.execute(delete(Bid))
    await db.execute(delete(Auction))
    await db.execute(delete(AgentPreference))
    await db.execute(delete(Agent))

    # Reset time slot statuses
    result = await db.execute(select(TimeSlot))
    for slot in result.scalars().all():
        slot.status = TimeSlotStatus.AVAILABLE

    await db.commit()
    return {"status": "reset_complete"}
