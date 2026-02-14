from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Agent,
    Auction,
    AuctionStatus,
    Bid,
    BidStatus,
    GroupBidMember,
    PriceHistory,
    Transaction,
)
from app.schemas.auction import BidCreate


class AuctionEngine(ABC):
    @abstractmethod
    async def start(self, auction: Auction, db: AsyncSession) -> None:
        pass

    @abstractmethod
    async def tick(self, auction: Auction, db: AsyncSession) -> None:
        pass

    @abstractmethod
    async def place_bid(self, auction: Auction, bid_data: BidCreate, db: AsyncSession) -> Bid:
        pass

    @abstractmethod
    async def resolve(self, auction: Auction, db: AsyncSession) -> None:
        pass


class DutchAuctionEngine(AuctionEngine):
    """Dutch auction: price starts high, decreases each tick until min_price,
    then increases. First bidder to accept current price wins."""

    async def start(self, auction: Auction, db: AsyncSession) -> None:
        auction.status = AuctionStatus.ACTIVE
        auction.started_at = datetime.utcnow()
        auction.current_price = auction.start_price

        # Record initial price
        history = PriceHistory(auction_id=auction.id, price=auction.current_price)
        db.add(history)

    async def tick(self, auction: Auction, db: AsyncSession) -> None:
        if auction.current_price > auction.min_price:
            # Decreasing phase
            auction.current_price = max(
                auction.current_price - auction.price_step,
                auction.min_price,
            )
        else:
            # Increasing phase (scarcity signal)
            auction.current_price = auction.current_price + auction.price_step

        # Record price tick
        history = PriceHistory(auction_id=auction.id, price=auction.current_price)
        db.add(history)

    async def place_bid(self, auction: Auction, bid_data: BidCreate, db: AsyncSession) -> Bid:
        # Validate agent
        result = await db.execute(select(Agent).where(Agent.id == bid_data.agent_id))
        agent = result.scalar_one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if bid_data.is_group_bid and bid_data.group_members:
            # Group bid: sum contributions
            total = sum(m.contribution for m in bid_data.group_members)
            if total < auction.current_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Group bid total {total} is below current price {auction.current_price}",
                )

            # Verify all members have sufficient balance
            for member in bid_data.group_members:
                m_result = await db.execute(select(Agent).where(Agent.id == member.agent_id))
                m_agent = m_result.scalar_one_or_none()
                if not m_agent:
                    raise HTTPException(status_code=404, detail=f"Agent {member.agent_id} not found")
                if m_agent.token_balance < member.contribution:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent {member.agent_id} has insufficient balance",
                    )

            # Create bid
            bid = Bid(
                auction_id=auction.id,
                agent_id=bid_data.agent_id,
                amount=total,
                is_group_bid=True,
                status=BidStatus.ACCEPTED,
            )
            db.add(bid)
            await db.flush()

            # Create group members and deduct tokens
            for member in bid_data.group_members:
                gm = GroupBidMember(
                    bid_id=bid.id,
                    agent_id=member.agent_id,
                    contribution=member.contribution,
                )
                db.add(gm)

                m_result = await db.execute(select(Agent).where(Agent.id == member.agent_id))
                m_agent = m_result.scalar_one()
                m_agent.token_balance -= member.contribution

                tx = Transaction(
                    agent_id=member.agent_id,
                    amount=-member.contribution,
                    type="bid_payment",
                    reference_id=bid.id,
                )
                db.add(tx)

        else:
            # Solo bid
            if bid_data.amount < auction.current_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bid amount {bid_data.amount} is below current price {auction.current_price}",
                )
            if agent.token_balance < bid_data.amount:
                raise HTTPException(status_code=400, detail="Insufficient token balance")

            bid = Bid(
                auction_id=auction.id,
                agent_id=bid_data.agent_id,
                amount=bid_data.amount,
                is_group_bid=False,
                status=BidStatus.ACCEPTED,
            )
            db.add(bid)
            await db.flush()

            # Deduct tokens
            agent.token_balance -= bid_data.amount
            tx = Transaction(
                agent_id=agent.id,
                amount=-bid_data.amount,
                type="bid_payment",
                reference_id=bid.id,
            )
            db.add(tx)

        return bid

    async def resolve(self, auction: Auction, db: AsyncSession) -> None:
        auction.status = AuctionStatus.COMPLETED
        auction.ended_at = datetime.utcnow()


_engines: dict[str, AuctionEngine] = {
    "dutch": DutchAuctionEngine(),
}


def get_auction_engine(auction_type: str) -> AuctionEngine:
    engine = _engines.get(auction_type)
    if not engine:
        raise HTTPException(status_code=400, detail=f"Unknown auction type: {auction_type}")
    return engine


def register_auction_engine(name: str, engine: AuctionEngine) -> None:
    _engines[name] = engine
