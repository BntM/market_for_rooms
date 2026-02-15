import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class AuctionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BidStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    time_slot_id: Mapped[str] = mapped_column(ForeignKey("time_slots.id"), nullable=False)
    auction_type: Mapped[str] = mapped_column(String, default="dutch")
    status: Mapped[AuctionStatus] = mapped_column(
        Enum(AuctionStatus), default=AuctionStatus.PENDING
    )
    start_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_step: Mapped[float] = mapped_column(Float, nullable=False)
    tick_interval_sec: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    time_slot: Mapped["TimeSlot"] = relationship(back_populates="auctions")  # noqa: F821
    bids: Mapped[list["Bid"]] = relationship(back_populates="auction", cascade="all, delete-orphan")
    price_history: Mapped[list["PriceHistory"]] = relationship(  # noqa: F821
        back_populates="auction", cascade="all, delete-orphan"
    )


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_group_bid: Mapped[bool] = mapped_column(Boolean, default=False)
    split_with_agent_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[BidStatus] = mapped_column(Enum(BidStatus), default=BidStatus.PENDING)
    placed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    auction: Mapped["Auction"] = relationship(back_populates="bids")
    agent: Mapped["Agent"] = relationship(back_populates="bids")  # noqa: F821
    group_members: Mapped[list["GroupBidMember"]] = relationship(
        back_populates="bid", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="bid")  # noqa: F821


class GroupBidMember(Base):
    __tablename__ = "group_bid_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    bid_id: Mapped[str] = mapped_column(ForeignKey("bids.id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)

    bid: Mapped["Bid"] = relationship(back_populates="group_members")
