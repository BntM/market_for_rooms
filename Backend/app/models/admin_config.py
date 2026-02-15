from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdminConfig(Base):
    __tablename__ = "admin_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    token_starting_amount: Mapped[float] = mapped_column(Float, default=100.0) # User starting balance
    token_frequency_days: Mapped[float] = mapped_column(Float, default=7.0) # Days between distributions
    token_inflation_rate: Mapped[float] = mapped_column(Float, default=0.0) # Percentage increase (e.g. 0.05 for 5%)
    max_bookings_per_agent: Mapped[int] = mapped_column(Integer, default=10)
    
    # Hidden Auction Params (Defaults)
    default_auction_type: Mapped[str] = mapped_column(String, default="dutch")
    dutch_start_price: Mapped[float] = mapped_column(Float, default=100.0)
    dutch_min_price: Mapped[float] = mapped_column(Float, default=10.0)
    dutch_price_step: Mapped[float] = mapped_column(Float, default=5.0)
    dutch_tick_interval_sec: Mapped[float] = mapped_column(Float, default=10.0)
    
    # Learned Data (Internal)
    location_popularity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_popularity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Sensitivities
    capacity_weight: Mapped[float] = mapped_column(Float, default=1.0)
    location_weight: Mapped[float] = mapped_column(Float, default=1.0)
    time_of_day_weight: Mapped[float] = mapped_column(Float, default=1.0) # Renamed from time_weight
    day_of_week_weight: Mapped[float] = mapped_column(Float, default=1.0) # New
    global_price_modifier: Mapped[float] = mapped_column(Float, default=1.0)
    lead_time_sensitivity: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Simulation State
    current_simulation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime(2026, 2, 14, 9, 0))
    pricing_model_version: Mapped[int] = mapped_column(Integer, default=1)
