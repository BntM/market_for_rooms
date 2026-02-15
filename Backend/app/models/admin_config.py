from sqlalchemy import Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdminConfig(Base):
    __tablename__ = "admin_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    token_allocation_amount: Mapped[float] = mapped_column(Float, default=100.0)
    token_allocation_frequency_hours: Mapped[float] = mapped_column(Float, default=24.0)
    max_bookings_per_agent: Mapped[int] = mapped_column(Integer, default=10)
    default_auction_type: Mapped[str] = mapped_column(String, default="dutch")
    dutch_start_price: Mapped[float] = mapped_column(Float, default=100.0)
    dutch_min_price: Mapped[float] = mapped_column(Float, default=10.0)
    dutch_price_step: Mapped[float] = mapped_column(Float, default=5.0)
    dutch_tick_interval_sec: Mapped[float] = mapped_column(Float, default=10.0)
    location_popularity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_popularity: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    capacity_weight: Mapped[float] = mapped_column(Float, default=1.0) # Sensitivity to capacity
    location_weight: Mapped[float] = mapped_column(Float, default=1.0) # Sensitivity to location
    time_weight: Mapped[float] = mapped_column(Float, default=1.0) # Sensitivity to time
    global_price_modifier: Mapped[float] = mapped_column(Float, default=1.0) # Scale curve up/down
