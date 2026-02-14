import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AdminConfig, Agent, AgentPreference


async def _get_config(db: AsyncSession) -> AdminConfig:
    result = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = result.scalar_one_or_none()
    if config is None:
        config = AdminConfig(id=1)
        db.add(config)
        await db.flush()
    return config


def _weighted_sample(popularity: dict[str, float]) -> tuple[str, float]:
    """Pick a value from the popularity distribution and return (value, weight).

    Higher-popularity items are more likely to be picked.  The returned
    weight reflects how strongly this agent prefers the chosen value
    (drawn uniformly in [0.3, 1.0] then scaled by the item's popularity).
    """
    items = list(popularity.keys())
    weights = [popularity[k] for k in items]
    chosen = random.choices(items, weights=weights, k=1)[0]
    raw_weight = random.uniform(0.3, 1.0)
    preference_weight = round(raw_weight * popularity[chosen], 3)
    return chosen, preference_weight


async def generate_preferences_for_agent(agent: Agent, db: AsyncSession) -> None:
    """Generate random preferences for an agent based on admin popularity config."""
    config = await _get_config(db)

    if config.location_popularity:
        value, weight = _weighted_sample(config.location_popularity)
        pref = AgentPreference(
            agent_id=agent.id,
            preference_type="location",
            preference_value=value,
            weight=weight,
        )
        db.add(pref)

    if config.time_popularity:
        # Give each agent 1-3 time preferences
        num_time_prefs = random.randint(1, 3)
        time_keys = list(config.time_popularity.keys())
        time_weights = [config.time_popularity[k] for k in time_keys]
        chosen_times = set()
        for _ in range(num_time_prefs):
            chosen = random.choices(time_keys, weights=time_weights, k=1)[0]
            if chosen not in chosen_times:
                chosen_times.add(chosen)
                raw_weight = random.uniform(0.3, 1.0)
                weight = round(raw_weight * config.time_popularity[chosen], 3)
                pref = AgentPreference(
                    agent_id=agent.id,
                    preference_type="time",
                    preference_value=chosen,
                    weight=weight,
                )
                db.add(pref)
