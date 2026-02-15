"""Pydantic schemas for PettingZoo simulation endpoints."""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class PZSimConfig(BaseModel):
    """Request body for running a simulation."""
    num_agents: int = 30
    num_rooms: int = 5
    slots_per_room_per_day: int = 3
    max_days: int = 14

    auction_start_price: float = 100.0
    auction_min_price: float = 10.0
    auction_price_step: float = 5.0
    max_ticks: int = 20

    high_demand_days: List[List[int]] = Field(default_factory=lambda: [[10, 14]])

    # For single sim
    token_amount: float = 100.0
    token_frequency: int = 7


class PZGridSearchRequest(BaseModel):
    """Request body for grid search."""
    config: PZSimConfig = Field(default_factory=PZSimConfig)
    token_amounts: List[float] = Field(default_factory=lambda: [50.0, 75.0, 100.0, 125.0, 150.0, 200.0])
    token_frequencies: List[int] = Field(default_factory=lambda: [3, 5, 7, 10, 14])
    num_seeds: int = 3


class PZMetricsResponse(BaseModel):
    supply_demand_ratio: float
    utilization_rate: float
    price_volatility: float
    unmet_demand: float
    gini_coefficient: float
    stability_score: float


class PZSingleResponse(BaseModel):
    metrics: PZMetricsResponse
    daily_detail: Dict[str, Dict[str, float]]


class PZGridSearchResult(BaseModel):
    token_amount: float
    token_frequency: int
    stability_score: float
    supply_demand_ratio: float
    utilization_rate: float
    price_volatility: float
    unmet_demand: float
    gini_coefficient: float


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
