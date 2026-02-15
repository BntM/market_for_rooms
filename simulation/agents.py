"""Rule-based agent strategies for the market simulation."""

import random
from typing import List

from .config import SimulationConfig
from .market_state import SimAgent, SimAuction


def generate_agents(config: SimulationConfig, rng: random.Random) -> List[SimAgent]:
    """Generate agents with preferences drawn from configured distributions."""
    agents = []
    num_locations = config.num_rooms
    loc_weights = config.location_weights[:num_locations]
    time_weights = config.time_weights

    for i in range(config.num_agents):
        preferred_time = _weighted_choice(list(range(len(time_weights))), time_weights, rng)
        preferred_location = _weighted_choice(list(range(num_locations)), loc_weights, rng)
        budget_sensitivity = rng.uniform(0.2, 0.9)
        urgency = rng.uniform(0.2, 0.8)
        base_value = rng.uniform(60.0, 100.0)

        agents.append(SimAgent(
            id=i,
            preferred_time=preferred_time,
            preferred_location=preferred_location,
            budget_sensitivity=budget_sensitivity,
            urgency=urgency,
            base_value=base_value,
        ))

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
