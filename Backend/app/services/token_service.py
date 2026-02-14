from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminConfig, Agent, Transaction


async def allocate_tokens(db: AsyncSession) -> list[Transaction]:
    """Allocate tokens to all active agents based on admin config."""
    cfg_result = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = cfg_result.scalar_one_or_none()
    if not config:
        config = AdminConfig(id=1)
        db.add(config)
        await db.flush()

    agents_result = await db.execute(select(Agent).where(Agent.is_active == True))
    agents = agents_result.scalars().all()

    transactions = []
    for agent in agents:
        agent.token_balance += config.token_allocation_amount
        tx = Transaction(
            agent_id=agent.id,
            amount=config.token_allocation_amount,
            type="allocation",
        )
        db.add(tx)
        transactions.append(tx)

    return transactions
