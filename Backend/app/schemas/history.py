from pydantic import BaseModel, Field
from typing import Dict, List, Optional

# --- Analysis Schemas ---
class AnalysisRequest(BaseModel):
    # We might accept a file upload directly, but if we pass parsed data:
    data: List[Dict[str, str]]

class AnalysisResponse(BaseModel):
    suggested_location_weights: Dict[str, float]
    suggested_time_weights: Dict[str, float]
    detected_events: List[Dict[str, float]] = []

# --- Simulation Schemas ---

class AgentConfig(BaseModel):
    name: str
    budget_mult: float = 1.0
    urgency_min: float = 0.1
    urgency_max: float = 1.0
    count: int = 10
    pref_location: Optional[str] = None
    # Granular Priorities (0.0 to 1.0)
    time_weight: float = 0.5
    day_weight: float = 0.5
    capacity_weight: float = 0.5
    location_weight: float = 0.5
    # Specific preferences
    preferred_days: List[int] = [] # 0=Mon, 6=Sun
    preferred_hours: List[int] = [] # 0-23

class SimulationConfig(BaseModel):
    days: int = 14
    base_price: float = 10.0
    token_drip: float = 5.0
    weights: Dict[str, Dict[str, float]]
    agent_configs: List[AgentConfig]
    events: Dict[int, float] = {} # Day index -> Demand Multiplier
    use_real_rooms: bool = True

class SimulationResult(BaseModel):
    day: int
    agent_id: str
    agent_type: str
    room_id: str
    price_paid: float
    tte: int
    revenue: float

class OptimizationRequest(SimulationConfig):
    price_range_start: int = 5
    price_range_end: int = 50
    price_step: int = 5

class OptimizationResponse(BaseModel):
    best_base_price: float
    max_revenue: float
    all_results: Dict[float, float] # price -> revenue
