"""Seed the database with test data."""
import asyncio
from datetime import datetime

from app.database import async_session, init_db
from app.models import (
    AdminConfig, Agent, Auction, AuctionStatus, Bid, BidStatus,
    LimitOrder, Resource, TimeSlot, Transaction,
)
from app.services.auction_engine import get_auction_engine
from app.services.booking_service import create_booking_from_bid
from app.utils import generate_uuid


async def seed():
    await init_db()

    async with async_session() as db:
        # 1. Admin config
        config = AdminConfig(
            id=1,
            token_allocation_amount=100,
            token_allocation_frequency_hours=24,
            dutch_start_price=80,
            dutch_min_price=5,
            dutch_price_step=3,
            dutch_tick_interval_sec=10,
            max_bookings_per_agent=10,
            location_popularity={"Building A": 0.5, "Building B": 0.35, "Building C": 0.15},
            time_popularity={"09:00": 0.2, "10:00": 0.25, "14:00": 0.2},
        )
        db.add(config)

        # 2. Rooms
        rooms = [
            Resource(name="Oak Room", location="Building A", capacity=4),
            Resource(name="Maple Room", location="Building A", capacity=2),
            Resource(name="Cedar Room", location="Building B", capacity=6),
            Resource(name="Birch Room", location="Building B", capacity=3),
            Resource(name="Pine Room", location="Building C", capacity=8),
        ]
        for r in rooms:
            db.add(r)
        await db.flush()
        print(f"Created {len(rooms)} rooms")

        # 3. Time slots (Feb 15, 9am-5pm, 30-min slots)
        from datetime import timedelta
        all_slots = []
        for room in rooms:
            base = datetime(2026, 2, 15, 9, 0, 0)
            for i in range(16):  # 16 half-hour slots from 9am to 5pm
                start = base + timedelta(minutes=30 * i)
                end = start + timedelta(minutes=30)
                slot = TimeSlot(resource_id=room.id, start_time=start, end_time=end)
                db.add(slot)
                all_slots.append((room, slot))
        await db.flush()
        print(f"Created {len(all_slots)} time slots")

        # 4. Agents
        agents = []
        for i in range(1, 7):
            agent = Agent(name=f"User_{i}", token_balance=500, max_bookings=10)
            db.add(agent)
            agents.append(agent)
        await db.flush()
        print(f"Created {len(agents)} agents")

        # 5. Create auctions for first 6 slots of each room (30 total)
        auctions = []
        engine = get_auction_engine("dutch")
        for room in rooms:
            room_slots = [s for r, s in all_slots if r.id == room.id][:6]
            for slot in room_slots:
                auction = Auction(
                    time_slot_id=slot.id,
                    auction_type="dutch",
                    start_price=80.0,
                    current_price=80.0,
                    min_price=5.0,
                    price_step=3.0,
                    tick_interval_sec=10.0,
                )
                db.add(auction)
                auctions.append(auction)
                slot.status = "in_auction"
        await db.flush()
        print(f"Created {len(auctions)} auctions")

        # 6. Start all auctions
        for auction in auctions:
            await engine.start(auction, db)
        await db.flush()
        print("Started all auctions")

        # 7. Tick 5 rounds to build price history
        for tick_round in range(5):
            for auction in auctions:
                if auction.status == AuctionStatus.ACTIVE:
                    await engine.tick(auction, db)
        await db.flush()
        print("Ticked 5 rounds (prices: 80 -> 65)")

        # 8. Place bids on first 6 auctions
        bid_count = 0
        for i, auction in enumerate(auctions[:6]):
            agent = agents[i % 3]
            price = auction.current_price
            bid = Bid(
                auction_id=auction.id,
                agent_id=agent.id,
                amount=price,
                is_group_bid=False,
                status=BidStatus.ACCEPTED,
            )
            db.add(bid)
            agent.token_balance -= price
            tx = Transaction(agent_id=agent.id, amount=-price, type="bid_payment", reference_id=bid.id)
            db.add(tx)
            await db.flush()
            await create_booking_from_bid(auction, bid, db)
            bid_count += 1
        await db.flush()
        print(f"Placed {bid_count} bids with bookings")

        # 9. Place limit orders on next 4 active auctions
        active_remaining = [a for a in auctions[6:] if a.status == AuctionStatus.ACTIVE]
        order_count = 0
        for i, auction in enumerate(active_remaining[:4]):
            agent = agents[4] if i % 2 == 0 else agents[5]
            max_price = 20 + i * 5
            order = LimitOrder(
                agent_id=agent.id,
                time_slot_id=auction.time_slot_id,
                max_price=max_price,
            )
            db.add(order)
            order_count += 1
        print(f"Placed {order_count} limit orders")

        # 10. Tick 3 more rounds to potentially trigger limit orders
        for tick_round in range(3):
            for auction in auctions:
                if auction.status == AuctionStatus.ACTIVE:
                    await engine.tick(auction, db)
        await db.flush()
        print("Ticked 3 more rounds")

        await db.commit()
        print("\n=== SEED COMPLETE ===")
        print(f"  Rooms: {len(rooms)}")
        print(f"  Time slots: {len(all_slots)}")
        print(f"  Agents: {len(agents)}")
        print(f"  Auctions: {len(auctions)}")
        print(f"  Bids/Bookings: {bid_count}")
        print(f"  Limit orders: {order_count}")
        for a in agents:
            print(f"  {a.name}: {a.token_balance:.0f} tokens")


if __name__ == "__main__":
    asyncio.run(seed())
