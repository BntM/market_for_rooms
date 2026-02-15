import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class LimitOrderStatus(str, enum.Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class LimitOrder(Base):
    __tablename__ = "limit_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    time_slot_id: Mapped[str] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[LimitOrderStatus] = mapped_column(
        Enum(LimitOrderStatus), default=LimitOrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bid_id: Mapped[str | None] = mapped_column(ForeignKey("bids.id"), nullable=True)

    agent: Mapped["Agent"] = relationship()  # noqa: F821
    time_slot: Mapped["TimeSlot"] = relationship()  # noqa: F821
    bid: Mapped["Bid"] = relationship()  # noqa: F821
