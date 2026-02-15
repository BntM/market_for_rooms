from pydantic import BaseModel


class AdminConfigResponse(BaseModel):
    id: int
    token_allocation_amount: float
    token_allocation_frequency_hours: float
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
    time_weight: float | None = 1.0
    global_price_modifier: float | None = 1.0
    lead_time_sensitivity: float | None = 1.0

    model_config = {"from_attributes": True}


class AdminConfigUpdate(BaseModel):
    token_allocation_amount: float | None = None
    token_allocation_frequency_hours: float | None = None
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
    time_weight: float | None = None
    global_price_modifier: float | None = None
    lead_time_sensitivity: float | None = None
