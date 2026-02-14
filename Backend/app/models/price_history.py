from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils import generate_uuid


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    auction: Mapped["Auction"] = relationship(back_populates="price_history")  # noqa: F821
