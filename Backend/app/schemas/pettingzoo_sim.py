"""Pydantic schemas for PettingZoo simulation endpoints."""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class PZAgentProfile(BaseModel):
    """Agent profile for Pareto-style tier distribution."""
    name: str = "default"
    share: float = 1.0
    urgency_range: List[float] = Field(default_factory=lambda: [0.2, 0.8])
    budget_sensitivity_range: List[float] = Field(default_factory=lambda: [0.2, 0.9])
    base_value_range: List[float] = Field(default_factory=lambda: [60.0, 100.0])


class PZSimConfig(BaseModel):
    """Request body for running a simulation."""
    num_agents: int = 30
    num_rooms: int = 5
    slots_per_room_per_day: int = 3
    max_days: int = 28

    auction_start_price: float = 100.0
    auction_min_price: float = 10.0
    auction_price_step: float = 5.0
    max_ticks: int = 20

    high_demand_days: List[List[int]] = Field(default_factory=lambda: [[20, 28]])

    # For single sim
    token_amount: float = 100.0
    token_frequency: int = 7

    # Agent profiles (Pareto tiers)
    agent_profiles: Optional[List[PZAgentProfile]] = None


class PZGridSearchRequest(BaseModel):
    """Request body for grid search."""
    config: PZSimConfig = Field(default_factory=PZSimConfig)
    token_amounts: List[float] = Field(default_factory=lambda: [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 300.0])
    token_frequencies: List[int] = Field(default_factory=lambda: [1, 2, 3, 5, 7, 10, 14])
    num_seeds: int = 5


class PZMetricsResponse(BaseModel):
    avg_satisfaction: float = 0.0
    preference_match_rate: float = 0.0
    avg_consumer_surplus: float = 0.0
    access_rate: float = 0.0
    utilization_rate: float = 0.0
    price_volatility: float = 0.0
    gini_coefficient: float = 0.0
    supply_demand_ratio: float = 0.0
    unmet_demand: float = 0.0
    stability_score: float = 0.0


class PZSingleResponse(BaseModel):
    metrics: PZMetricsResponse
    daily_detail: Dict[str, Dict[str, float]]


class PZGridSearchResult(BaseModel):
    token_amount: float
    token_frequency: int
    stability_score: float
    avg_satisfaction: float = 0.0
    preference_match_rate: float = 0.0
    access_rate: float = 0.0
    utilization_rate: float = 0.0
    price_volatility: float = 0.0
    gini_coefficient: float = 0.0
    supply_demand_ratio: float = 0.0
    unmet_demand: float = 0.0


class PZGridSearchResponse(BaseModel):
    best: Optional[PZGridSearchResult] = None
    best_daily: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    all_results: List[PZGridSearchResult] = Field(default_factory=list)
    heatmap: Dict[str, Any] = Field(default_factory=dict)


class PZJobStatus(BaseModel):
    job_id: str
    status: str  # "running", "completed", "failed"
    progress: float = 0.0
    result: Optional[PZGridSearchResponse] = None
    error: Optional[str] = None


class PZApplyRequest(BaseModel):
    token_amount: float
    token_frequency: int
