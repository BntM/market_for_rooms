"""Pure Python domain objects for the market simulation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SimRoom:
    id: int
    name: str
    location_index: int  # index into location_weights


@dataclass
class SimTimeSlot:
    id: int
    room_id: int
    day: int
    time_index: int  # 0=morning, 1=afternoon, 2=evening


@dataclass
class SimAuction:
    id: int
    slot_id: int
    room_id: int
    day: int
    time_index: int
    location_index: int
    start_price: float
    min_price: float
    price_step: float
    current_price: float
    completed: bool = False
    winner_id: Optional[int] = None
    clearing_price: Optional[float] = None
    tick: int = 0


@dataclass
class SimAgent:
    id: int
    preferred_time: int  # 0=morning, 1=afternoon, 2=evening
    preferred_location: int  # index into rooms
    budget_sensitivity: float  # 0.0 (price insensitive) to 1.0 (very sensitive)
    urgency: float  # 0.0 to 1.0
    base_value: float = 80.0  # base WTP for an ideal slot
    balance: float = 0.0
    bookings: List[int] = field(default_factory=list)  # slot ids


@dataclass
class SimBooking:
    agent_id: int
    slot_id: int
    price: float
    day: int


@dataclass
class MarketState:
    """Tracks the full state of the simulated market."""
    rooms: List[SimRoom] = field(default_factory=list)
    agents: List[SimAgent] = field(default_factory=list)
    slots: Dict[int, SimTimeSlot] = field(default_factory=dict)
    bookings: List[SimBooking] = field(default_factory=list)

    # Daily tracking
    daily_auctions: Dict[int, List[SimAuction]] = field(default_factory=dict)  # day -> auctions
    daily_clearing_prices: Dict[int, List[float]] = field(default_factory=dict)
    daily_utilization: Dict[int, float] = field(default_factory=dict)
    daily_unmet_demand: Dict[int, int] = field(default_factory=dict)

    # Counters
    total_slots_offered: int = 0
    total_bids_attempted: int = 0
    total_slots_booked: int = 0

    auction_id_counter: int = 0
    slot_id_counter: int = 0

    def next_auction_id(self) -> int:
        self.auction_id_counter += 1
        return self.auction_id_counter

    def next_slot_id(self) -> int:
        self.slot_id_counter += 1
        return self.slot_id_counter
