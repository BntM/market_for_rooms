# RL Agent Integration Guide

This guide explains how the RL team should interface with the market backend to build agent bidding strategies.

## Overview

The market backend provides a REST API that your RL agents interact with. Each agent:
1. Receives tokens periodically (via the simulation round or manual allocation)
2. Observes the market state (active auctions, current prices, available slots)
3. Decides whether/when to bid and how much to bid
4. Receives bookings for winning bids

## Setup

```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs at: `http://localhost:8000/docs`

## Core Workflow

### 1. Register Agents

**Single agent:**
```
POST /api/agents/
{
  "name": "rl_agent_1",
  "token_balance": 0.0,
  "max_bookings": 10
}
```

**Bulk with auto-generated preferences:**
```
POST /api/agents/bulk
{
  "count": 50,
  "name_prefix": "Student",
  "initial_balance": 0.0,
  "max_bookings": 10,
  "generate_preferences": true
}
```

Preferences are generated from admin-configured popularity distributions. See "Preference System" below.

### 2. Observe Market State

**Get all active auctions:**
```
GET /api/auctions/?status=active
```

**Get a specific auction (includes current price):**
```
GET /api/auctions/{auction_id}
```

Response:
```json
{
  "id": "...",
  "time_slot_id": "...",
  "auction_type": "dutch",
  "status": "active",
  "start_price": 100.0,
  "current_price": 75.0,
  "min_price": 10.0,
  "price_step": 5.0,
  "tick_interval_sec": 10.0
}
```

**Get full market overview:**
```
GET /api/market/state
```

**Get agent's current balance and info:**
```
GET /api/agents/{agent_id}
```

**Get agent's preferences (to inform bidding strategy):**
```
GET /api/agents/{agent_id}/preferences
```

### 3. Place Bids

**Solo bid:**
```
POST /api/auctions/{auction_id}/bid
{
  "agent_id": "...",
  "amount": 75.0
}
```

The bid must be >= the auction's `current_price`. Tokens are deducted immediately on acceptance.

**Group bid (token pooling):**
```
POST /api/auctions/{auction_id}/bid
{
  "agent_id": "lead_agent_id",
  "amount": 0,
  "is_group_bid": true,
  "group_members": [
    {"agent_id": "agent_1", "contribution": 30.0},
    {"agent_id": "agent_2", "contribution": 25.0},
    {"agent_id": "agent_3", "contribution": 20.0}
  ]
}
```

All members' contributions are summed and must meet the current price. All members get a booking if accepted.

### 4. Check Results

**Agent's bookings:**
```
GET /api/agents/{agent_id}/bookings
```

**Agent's transaction history:**
```
GET /api/agents/{agent_id}/transactions
```

**Price history for an auction:**
```
GET /api/auctions/{auction_id}/price-history
```

## Preference System

Each agent has preferences with types and weights:

| Type | Value Example | Weight |
|------|--------------|--------|
| `location` | `"Building A"` | 0.0–1.0 |
| `time` | `"09:00"` | 0.0–1.0 |

Higher weight = stronger preference. Use these to inform your bidding strategy (e.g., bid more aggressively for preferred slots).

The admin configures popularity distributions:
```json
{
  "location_popularity": {"Building A": 0.7, "Building B": 0.3},
  "time_popularity": {"09:00": 0.9, "10:00": 0.7, "14:00": 0.4}
}
```

When agents are bulk-generated, their preferences are sampled from these distributions.

## Dutch Auction Mechanics

1. Price starts at `start_price` (e.g., 100 tokens)
2. Each tick: price decreases by `price_step` (e.g., -5 tokens)
3. Once price hits `min_price`: price starts **increasing** (scarcity signal)
4. First bid at or above `current_price` wins
5. The RL decision: **when to bid** — too early = overpay, too late = someone else wins or price rises

## Simulation Loop

For training, use the simulation endpoints:

```
POST /api/simulation/round        # Run one round (allocate tokens + tick auctions)
POST /api/simulation/allocate-tokens  # Just allocate tokens
POST /api/auctions/{id}/tick      # Tick a specific auction
GET  /api/simulation/results      # Get metrics
POST /api/simulation/reset        # Reset all agents/auctions (keeps rooms)
```

### Typical Training Loop:
1. `POST /api/simulation/agents/generate` — create agents
2. `POST /api/simulation/allocate-tokens` — give agents tokens
3. Create auctions for time slots
4. Loop:
   - `POST /api/auctions/{id}/tick` — advance price
   - Your RL agents observe and decide to bid (or wait)
   - `POST /api/auctions/{id}/bid` — place bids
5. `GET /api/simulation/results` — evaluate
6. `POST /api/simulation/reset` — reset for next episode

## Key Constraints

- Agent cannot book two rooms in the same time slot
- Agent cannot exceed `max_bookings` total
- Room cannot exceed `capacity` concurrent bookings per slot
- Bid must meet or exceed `current_price`
- Agent must have sufficient token balance
