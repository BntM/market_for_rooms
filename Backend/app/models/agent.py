from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    token_balance: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_bookings: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    preferences: Mapped[list["AgentPreference"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    bids: Mapped[list["Bid"]] = relationship(back_populates="agent")  # noqa: F821
    bookings: Mapped[list["Booking"]] = relationship(back_populates="agent")  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="agent")  # noqa: F821


class AgentPreference(Base):
    __tablename__ = "agent_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    preference_type: Mapped[str] = mapped_column(String, nullable=False)
    preference_value: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=0.5)

    agent: Mapped["Agent"] = relationship(back_populates="preferences")
