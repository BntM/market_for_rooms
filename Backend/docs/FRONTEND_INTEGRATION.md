# Frontend Integration Guide

This guide explains the API endpoints available for building the admin dashboard and student-facing UI.

## Setup

Backend runs at `http://localhost:8000`. CORS is enabled for all origins. Interactive API docs at `/docs`.

## Admin Dashboard

### Configuration

**Get current config:**
```
GET /api/admin/config
```

**Update config:**
```
PUT /api/admin/config
{
  "token_allocation_amount": 100.0,
  "token_allocation_frequency_hours": 24.0,
  "max_bookings_per_agent": 10,
  "default_auction_type": "dutch",
  "dutch_start_price": 100.0,
  "dutch_min_price": 10.0,
  "dutch_price_step": 5.0,
  "dutch_tick_interval_sec": 10.0,
  "location_popularity": {"Building A": 0.7, "Building B": 0.3},
  "time_popularity": {"09:00": 0.9, "10:00": 0.7, "14:00": 0.4}
}
```

All fields are optional — only send what you want to change.

### Room/Resource Management

**Create a room:**
```
POST /api/resources/
{
  "name": "Room A-101",
  "resource_type": "room",
  "location": "Building A",
  "capacity": 4,
  "attributes": {"has_whiteboard": true, "has_projector": false}
}
```

**List rooms (with optional filters):**
```
GET /api/resources/?resource_type=room&location=Building%20A
```

**Update a room:**
```
PUT /api/resources/{id}
{"name": "Room A-101 (Renovated)", "capacity": 6}
```

**Delete a room:**
```
DELETE /api/resources/{id}
```

### Time Slot Generation

**Generate 30-minute slots for a date range:**
```
POST /api/resources/{id}/timeslots/generate
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-07",
  "daily_start_hour": 8,
  "daily_end_hour": 22
}
```

This creates slots from 8:00 AM to 10:00 PM in 30-min increments for each day.

**List time slots:**
```
GET /api/resources/{id}/timeslots?status=available
```

### Simulation Controls

```
POST /api/simulation/agents/generate  — bulk create agents
POST /api/simulation/allocate-tokens  — distribute tokens
POST /api/simulation/round            — run one simulation round
GET  /api/simulation/results          — get metrics
POST /api/simulation/reset            — reset simulation data
```

### Market Overview

```
GET /api/market/state       — active auctions, counts
GET /api/market/price-history?limit=100 — recent price ticks
GET /api/market/resources   — all active resources
GET /api/market/resources/{id}/schedule — room schedule with bookings
```

## Student-Facing UI

### Agent/Student Endpoints

**Get agent info (balance, bookings limit):**
```
GET /api/agents/{agent_id}
```

Response:
```json
{
  "id": "abc-123",
  "name": "Student_1",
  "token_balance": 85.5,
  "is_active": true,
  "max_bookings": 10,
  "created_at": "2026-03-01T00:00:00"
}
```

**View my bookings:**
```
GET /api/agents/{agent_id}/bookings
```

**View my transaction history:**
```
GET /api/agents/{agent_id}/transactions
```

### Browsing & Bidding

**List available rooms:**
```
GET /api/market/resources
```

**View room schedule (see which slots are open):**
```
GET /api/market/resources/{resource_id}/schedule
```

Returns an array of `{slot, bookings}` objects showing availability.

**List active auctions:**
```
GET /api/auctions/?status=active
```

**View auction detail (current price):**
```
GET /api/auctions/{auction_id}
```

**Place a bid:**
```
POST /api/auctions/{auction_id}/bid
{
  "agent_id": "my-agent-id",
  "amount": 50.0
}
```

**View price history (for a chart):**
```
GET /api/auctions/{auction_id}/price-history
```

## Data Models

### Resource
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique identifier |
| name | string | Display name |
| resource_type | string | "room", "gpu", etc. |
| location | string | Building/area |
| capacity | int | Max concurrent users |
| attributes | object | Extensible metadata |
| is_active | bool | Whether available |

### TimeSlot
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | |
| resource_id | string | FK to resource |
| start_time | datetime | |
| end_time | datetime | Always start + 30 min |
| status | string | "available", "in_auction", "booked" |

### Auction
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | |
| time_slot_id | string | FK to time slot |
| auction_type | string | "dutch" (default) |
| status | string | "pending", "active", "completed", "cancelled" |
| current_price | float | Current asking price |
| start_price | float | Initial price |
| min_price | float | Floor before price rises |

### Booking
| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | |
| time_slot_id | string | |
| agent_id | string | |
| bid_id | string | Winning bid reference |
| created_at | datetime | |

## Error Handling

All errors return:
```json
{
  "detail": "Human-readable error message"
}
```

Common status codes:
- `400` — validation error (insufficient balance, capacity exceeded, etc.)
- `404` — resource not found
- `201` — created successfully
- `204` — deleted successfully
