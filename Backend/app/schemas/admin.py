from datetime import datetime
from pydantic import BaseModel


class AdminConfigResponse(BaseModel):
    id: int
    token_starting_amount: float
    token_frequency_days: float
    token_inflation_rate: float
    max_bookings_per_agent: int
    default_auction_type: str
    dutch_start_price: float
    dutch_min_price: float
    dutch_price_step: float
    dutch_tick_interval_sec: float
    location_popularity: dict | None = None
    time_popularity: dict | None = None
    capacity_weight: float | None = 1.0
    location_weight: float | None = 1.0
    time_of_day_weight: float | None = 1.0
    day_of_week_weight: float | None = 1.0
    global_price_modifier: float | None = 1.0
    lead_time_sensitivity: float | None = 1.0
    current_simulation_date: datetime | None = None
    pricing_model_version: int | None = 1

    model_config = {"from_attributes": True}


class AdminConfigUpdate(BaseModel):
    token_starting_amount: float | None = None
    token_frequency_days: float | None = None
    token_inflation_rate: float | None = None
    max_bookings_per_agent: int | None = None
    default_auction_type: str | None = None
    dutch_start_price: float | None = None
    dutch_min_price: float | None = None
    dutch_price_step: float | None = None
    dutch_tick_interval_sec: float | None = None
    location_popularity: dict | None = None
    time_popularity: dict | None = None
    capacity_weight: float | None = None
    location_weight: float | None = None
    time_of_day_weight: float | None = None
    day_of_week_weight: float | None = None
    global_price_modifier: float | None = None
    lead_time_sensitivity: float | None = None
    current_simulation_date: datetime | None = None
    pricing_model_version: int | None = None
