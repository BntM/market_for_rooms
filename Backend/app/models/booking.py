from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    time_slot_id: Mapped[str] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    bid_id: Mapped[str] = mapped_column(ForeignKey("bids.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    time_slot: Mapped["TimeSlot"] = relationship(back_populates="bookings")  # noqa: F821
    agent: Mapped["Agent"] = relationship(back_populates="bookings")  # noqa: F821
    bid: Mapped["Bid"] = relationship(back_populates="bookings")  # noqa: F821
