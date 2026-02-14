from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Agent, AgentPreference, Booking, Transaction
from app.schemas.agent import (
    AgentCreate,
    AgentPreferenceCreate,
    AgentPreferenceResponse,
    AgentResponse,
    BulkAgentCreate,
    TransactionResponse,
)
from app.schemas.auction import BookingResponse
from app.services.preference_generator import generate_preferences_for_agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(**data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/bulk", response_model=list[AgentResponse], status_code=201)
async def create_agents_bulk(data: BulkAgentCreate, db: AsyncSession = Depends(get_db)):
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


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Agent)
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/preferences", response_model=list[AgentPreferenceResponse])
async def get_preferences(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentPreference).where(AgentPreference.agent_id == agent_id)
    )
    return result.scalars().all()


@router.put("/{agent_id}/preferences", response_model=list[AgentPreferenceResponse])
async def set_preferences(
    agent_id: str,
    preferences: list[AgentPreferenceCreate],
    db: AsyncSession = Depends(get_db),
):
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    # Delete existing preferences
    existing = await db.execute(
        select(AgentPreference).where(AgentPreference.agent_id == agent_id)
    )
    for pref in existing.scalars().all():
        await db.delete(pref)

    # Create new preferences
    new_prefs = []
    for p in preferences:
        pref = AgentPreference(agent_id=agent_id, **p.model_dump())
        db.add(pref)
        new_prefs.append(pref)

    await db.commit()
    for pref in new_prefs:
        await db.refresh(pref)
    return new_prefs


@router.get("/{agent_id}/bookings", response_model=list[BookingResponse])
async def get_agent_bookings(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.agent_id == agent_id))
    return result.scalars().all()


@router.get("/{agent_id}/transactions", response_model=list[TransactionResponse])
async def get_agent_transactions(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.agent_id == agent_id)
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()
