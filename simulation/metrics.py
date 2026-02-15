"""Stability metrics for evaluating market simulation outcomes."""

import math
from dataclasses import dataclass, field
from typing import Dict, List

from .market_state import MarketState


@dataclass
class StabilityMetrics:
    supply_demand_ratio: float = 0.0  # total_slots / total_bids (ideal ~1.0)
    utilization_rate: float = 0.0  # booked / offered (ideal 0.7-0.9)
    price_volatility: float = 0.0  # CV of clearing prices (lower = better)
    unmet_demand: float = 0.0  # fraction of agents who wanted but couldn't book
    gini_coefficient: float = 0.0  # booking inequality (lower = more equitable)
    stability_score: float = 0.0  # weighted composite (lower = better)

    # Daily breakdowns for charts
    daily_utilization: Dict[int, float] = field(default_factory=dict)
    daily_avg_price: Dict[int, float] = field(default_factory=dict)


def compute_metrics(state: MarketState, num_agents: int) -> StabilityMetrics:
    """Compute stability metrics from a completed simulation."""
    m = StabilityMetrics()

    # Supply/demand ratio
    if state.total_bids_attempted > 0:
        m.supply_demand_ratio = state.total_slots_offered / state.total_bids_attempted
    else:
        m.supply_demand_ratio = float('inf')

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

    # Unmet demand: fraction of agents with 0 bookings
    agents_with_bookings = len(set(b.agent_id for b in state.bookings))
    if num_agents > 0:
        m.unmet_demand = 1.0 - (agents_with_bookings / num_agents)
    else:
        m.unmet_demand = 0.0

    # Gini coefficient of bookings per agent
    booking_counts = [0] * num_agents
    for b in state.bookings:
        if b.agent_id < num_agents:
            booking_counts[b.agent_id] += 1
    m.gini_coefficient = _gini(booking_counts)

    # Daily breakdowns
    m.daily_utilization = dict(state.daily_utilization)
    m.daily_avg_price = {}
    for day, prices in state.daily_clearing_prices.items():
        m.daily_avg_price[day] = sum(prices) / len(prices) if prices else 0.0

    # Composite stability score (lower = better)
    # Penalize deviation from ideal supply/demand ratio of 1.0
    sd_penalty = abs(m.supply_demand_ratio - 1.0) * 2.0 if m.supply_demand_ratio != float('inf') else 5.0
    # Penalize deviation from ideal utilization of 0.8
    util_penalty = abs(m.utilization_rate - 0.8) * 3.0
    # Penalize high price volatility
    vol_penalty = m.price_volatility * 1.5
    # Penalize unmet demand
    unmet_penalty = m.unmet_demand * 2.0
    # Penalize inequality
    gini_penalty = m.gini_coefficient * 1.0

    m.stability_score = sd_penalty + util_penalty + vol_penalty + unmet_penalty + gini_penalty

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
