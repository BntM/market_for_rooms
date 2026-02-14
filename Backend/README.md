# Market for Rooms — Backend

A token-based market backend for booking study rooms (and other resources) using auctions. Agents/students receive tokens and bid on room time slots through a Dutch auction mechanism.

## Quick Start

```bash
cd Backend
python3.13 -m venv .venv       # Python 3.11-3.13 recommended
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## Architecture

```
app/
├── main.py          # FastAPI app, CORS, router registration
├── config.py        # Environment-based settings
├── database.py      # SQLAlchemy async engine + session
├── models/          # ORM models (Resource, Agent, Auction, Bid, Booking, etc.)
├── schemas/         # Pydantic request/response schemas
├── routers/         # API endpoints grouped by domain
│   ├── admin.py     # Config management
│   ├── resources.py # Room CRUD + time slot generation
│   ├── agents.py    # Agent CRUD + preferences + transactions
│   ├── auctions.py  # Auction lifecycle + bidding
│   ├── market.py    # Market state + price history
│   └── simulation.py # Simulation controls
└── services/        # Business logic
    ├── auction_engine.py       # Pluggable auction (Dutch default)
    ├── booking_service.py      # Booking constraints
    ├── token_service.py        # Token allocation
    ├── preference_generator.py # Random preferences from distributions
    └── simulation_service.py   # Simulation round runner
```

## Key Concepts

- **Resources**: Bookable items (rooms, GPUs). Each has a capacity, location, and type.
- **Time Slots**: 30-minute intervals generated for each resource.
- **Tokens**: Currency agents use to bid. Allocated periodically by the system.
- **Dutch Auction**: Price starts high, decreases each tick, then increases after hitting a floor. First bidder to accept wins.
- **Group Bidding**: Multiple agents pool tokens to bid together; all get bookings.

## Integration Docs

- [RL Agent Integration](docs/RL_INTEGRATION.md) — for the RL team
- [Frontend Integration](docs/FRONTEND_INTEGRATION.md) — for the frontend team

## Adding New Auction Types

Subclass `AuctionEngine` in `app/services/auction_engine.py`:

```python
from app.services.auction_engine import AuctionEngine, register_auction_engine

class SealedBidEngine(AuctionEngine):
    async def start(self, auction, db): ...
    async def tick(self, auction, db): ...
    async def place_bid(self, auction, bid_data, db): ...
    async def resolve(self, auction, db): ...

register_auction_engine("sealed_bid", SealedBidEngine())
```

## Database

SQLite by default (file: `market.db`). Tables are auto-created on startup. To change the database URL, set the `MARKET_DATABASE_URL` environment variable.
