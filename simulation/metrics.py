"""Metrics for evaluating market simulation outcomes, optimized for agent satisfaction."""

import math
from dataclasses import dataclass, field
from typing import Dict, List

from .market_state import MarketState


@dataclass
class StabilityMetrics:
    # Agent satisfaction metrics (primary)
    avg_satisfaction: float = 0.0  # composite agent satisfaction 0-1 (higher = better)
    preference_match_rate: float = 0.0  # fraction of bookings matching preferred time+location
    avg_consumer_surplus: float = 0.0  # avg (WTP - price), higher = agents getting good deals
    access_rate: float = 0.0  # fraction of agents who booked at least once

    # Market health metrics (secondary)
    utilization_rate: float = 0.0  # booked / offered
    price_volatility: float = 0.0  # CV of clearing prices (lower = more predictable)
    gini_coefficient: float = 0.0  # booking inequality (lower = more equitable)

    # Legacy (kept for API compatibility)
    supply_demand_ratio: float = 0.0
    unmet_demand: float = 0.0
    stability_score: float = 0.0  # composite score (lower = better)

    # Daily breakdowns for charts
    daily_utilization: Dict[int, float] = field(default_factory=dict)
    daily_avg_price: Dict[int, float] = field(default_factory=dict)


def compute_metrics(state: MarketState, num_agents: int) -> StabilityMetrics:
    """Compute metrics from a completed simulation, weighted toward agent satisfaction."""
    m = StabilityMetrics()

    # --- Agent satisfaction metrics ---

    # Access rate: fraction of agents who got at least one booking
    agents_with_bookings = len(set(b.agent_id for b in state.bookings))
    m.access_rate = agents_with_bookings / num_agents if num_agents > 0 else 0.0

    # Preference match rate: how often agents got their preferred time AND location
    if state.bookings:
        time_matches = sum(1 for b in state.bookings if b.preferred_time_match)
        loc_matches = sum(1 for b in state.bookings if b.preferred_location_match)
        both_matches = sum(1 for b in state.bookings
                          if b.preferred_time_match and b.preferred_location_match)
        total = len(state.bookings)
        # Weighted: full match counts 1.0, partial match counts 0.5
        m.preference_match_rate = (both_matches + 0.5 * (time_matches + loc_matches - 2 * both_matches)) / total
    else:
        m.preference_match_rate = 0.0

    # Average consumer surplus (normalized by start price for comparability)
    if state.bookings:
        m.avg_consumer_surplus = sum(b.consumer_surplus for b in state.bookings) / len(state.bookings)
    else:
        m.avg_consumer_surplus = 0.0

    # --- Market health metrics ---

    # Utilization rate
    if state.total_slots_offered > 0:
        m.utilization_rate = state.total_slots_booked / state.total_slots_offered
    else:
        m.utilization_rate = 0.0

    # Price volatility (coefficient of variation)
    all_prices = []
    for prices in state.daily_clearing_prices.values():
        all_prices.extend(prices)

    if len(all_prices) >= 2:
        mean_price = sum(all_prices) / len(all_prices)
        if mean_price > 0:
            variance = sum((p - mean_price) ** 2 for p in all_prices) / len(all_prices)
            m.price_volatility = math.sqrt(variance) / mean_price
        else:
            m.price_volatility = 0.0
    else:
        m.price_volatility = 0.0

    # Gini coefficient of bookings per agent
    booking_counts = [0] * num_agents
    for b in state.bookings:
        if b.agent_id < num_agents:
            booking_counts[b.agent_id] += 1
    m.gini_coefficient = _gini(booking_counts)

    # --- Legacy metrics (kept for API compat) ---
    if state.total_bids_attempted > 0:
        m.supply_demand_ratio = state.total_slots_offered / state.total_bids_attempted
    else:
        m.supply_demand_ratio = float('inf')

    m.unmet_demand = 1.0 - m.access_rate

    # --- Daily breakdowns ---
    m.daily_utilization = dict(state.daily_utilization)
    m.daily_avg_price = {}
    for day, prices in state.daily_clearing_prices.items():
        m.daily_avg_price[day] = sum(prices) / len(prices) if prices else 0.0

    # --- Composite score (lower = better, optimized for agent satisfaction) ---
    # Access: heavily penalize when agents can't book at all
    access_penalty = (1.0 - m.access_rate) * 4.0
    # Preference: penalize poor preference matching
    pref_penalty = (1.0 - m.preference_match_rate) * 2.0
    # Fairness: penalize hoarding
    gini_penalty = m.gini_coefficient * 2.0
    # Utilization: lightly penalize waste (empty rooms = missed satisfaction)
    util_penalty = (1.0 - m.utilization_rate) * 1.0
    # Price predictability: light penalty for volatile prices (confuses agents)
    vol_penalty = m.price_volatility * 0.5

    m.stability_score = access_penalty + pref_penalty + gini_penalty + util_penalty + vol_penalty

    # Composite satisfaction 0-1 (higher = better) for easy interpretation
    # Weighted average of the key satisfaction dimensions
    m.avg_satisfaction = (
        0.35 * m.access_rate +
        0.25 * m.preference_match_rate +
        0.20 * (1.0 - m.gini_coefficient) +
        0.10 * m.utilization_rate +
        0.10 * max(0.0, 1.0 - m.price_volatility)
    )

    return m


def _gini(values: List[int]) -> float:
    """Compute Gini coefficient for a list of values."""
    n = len(values)
    if n == 0:
        return 0.0
    sorted_vals = sorted(values)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cumulative = 0.0
    gini_sum = 0.0
    for i, v in enumerate(sorted_vals):
        cumulative += v
        gini_sum += cumulative
    return 1.0 - (2.0 * gini_sum) / (n * total) + 1.0 / n
