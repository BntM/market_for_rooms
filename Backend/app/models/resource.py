import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class TimeSlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_AUCTION = "in_auction"
    BOOKED = "booked"


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False, default="room")
    location: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    time_slots: Mapped[list["TimeSlot"]] = relationship(back_populates="resource", cascade="all, delete-orphan")


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[TimeSlotStatus] = mapped_column(
        Enum(TimeSlotStatus), default=TimeSlotStatus.AVAILABLE
    )

    resource: Mapped["Resource"] = relationship(back_populates="time_slots")
    auctions: Mapped[list["Auction"]] = relationship(back_populates="time_slot")  # noqa: F821
    bookings: Mapped[list["Booking"]] = relationship(back_populates="time_slot")  # noqa: F821

    @property
    def booked_agent_ids(self) -> list[str]:
        try:
            return [b.agent_id for b in self.bookings]
        except:
            return []
