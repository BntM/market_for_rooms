"""Rule-based agent strategies for the market simulation."""

import random
from typing import List

from .config import AgentProfile, SimulationConfig
from .market_state import SimAgent, SimAuction


def generate_agents(config: SimulationConfig, rng: random.Random) -> List[SimAgent]:
    """Generate agents with preferences drawn from configured distributions.

    Uses agent_profiles to create Pareto-style tiers where heavy users
    (small share) have high urgency and low price sensitivity.
    """
    agents = []
    num_locations = config.num_rooms
    loc_weights = config.location_weights[:num_locations]
    time_weights = config.time_weights

    agent_id = 0
    for profile in config.agent_profiles:
        count = round(profile.share * config.num_agents)
        for _ in range(count):
            preferred_time = _weighted_choice(list(range(len(time_weights))), time_weights, rng)
            preferred_location = _weighted_choice(list(range(num_locations)), loc_weights, rng)
            budget_sensitivity = rng.uniform(*profile.budget_sensitivity_range)
            urgency = rng.uniform(*profile.urgency_range)
            base_value = rng.uniform(*profile.base_value_range)

            agents.append(SimAgent(
                id=agent_id,
                preferred_time=preferred_time,
                preferred_location=preferred_location,
                budget_sensitivity=budget_sensitivity,
                urgency=urgency,
                base_value=base_value,
            ))
            agent_id += 1

    return agents


def compute_utility(agent: SimAgent, auction: SimAuction, is_high_demand: bool) -> float:
    """Compute willingness-to-pay for an auction slot."""
    # Location preference multiplier
    if auction.location_index == agent.preferred_location:
        location_mult = 1.0
    else:
        location_mult = 0.5

    # Time preference multiplier
    if auction.time_index == agent.preferred_time:
        time_mult = 1.0
    else:
        time_mult = 0.6

    # Urgency multiplier (higher urgency = willing to pay more)
    urgency_mult = 0.7 + 0.6 * agent.urgency

    # High-demand multiplier (exam periods increase WTP)
    high_demand_mult = 1.4 if is_high_demand else 1.0

    # Booking need: agents with fewer bookings want rooms more
    booking_need = max(1.0, 1.5 - 0.1 * len(agent.bookings))

    wtp = agent.base_value * location_mult * time_mult * urgency_mult * high_demand_mult * booking_need
    return wtp


def should_bid(agent: SimAgent, auction: SimAuction, is_high_demand: bool) -> bool:
    """Decide if agent should bid at the current auction price."""
    if auction.completed:
        return False
    if agent.balance < auction.current_price:
        return False

    wtp = compute_utility(agent, auction, is_high_demand)

    # Budget sensitivity scales down WTP (sensitive agents wait for lower prices)
    adjusted_wtp = wtp * (1.0 - 0.5 * agent.budget_sensitivity)

    return auction.current_price <= adjusted_wtp


def _weighted_choice(items: list, weights: list, rng: random.Random):
    """Weighted random choice using the provided RNG."""
    total = sum(weights)
    r = rng.uniform(0, total)
    cumulative = 0.0
    for item, w in zip(items, weights):
        cumulative += w
        if r <= cumulative:
            return item
    return items[-1]
