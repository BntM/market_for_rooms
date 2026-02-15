from datetime import datetime

from pydantic import BaseModel


class AuctionCreate(BaseModel):
    time_slot_id: str
    auction_type: str = "dutch"
    start_price: float | None = None
    min_price: float | None = None
    price_step: float | None = None
    tick_interval_sec: float | None = None


from app.schemas.resource import TimeSlotResponse

class AuctionResponse(BaseModel):
    id: str
    time_slot_id: str
    auction_type: str
    status: str
    start_price: float
    current_price: float
    min_price: float
    price_step: float
    tick_interval_sec: float
    created_at: datetime
    started_at: datetime | None = None
    ended_at: datetime | None = None
    time_slot: TimeSlotResponse | None = None

    model_config = {"from_attributes": True}


class BidCreate(BaseModel):
    agent_id: str
    amount: float
    is_group_bid: bool = False
    group_members: list["GroupMemberContribution"] | None = None


class GroupMemberContribution(BaseModel):
    agent_id: str
    contribution: float


class BidResponse(BaseModel):
    id: str
    auction_id: str
    agent_id: str
    amount: float
    is_group_bid: bool
    status: str
    placed_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryResponse(BaseModel):
    id: str
    auction_id: str
    price: float
    recorded_at: datetime

    model_config = {"from_attributes": True}


class BookingResponse(BaseModel):
    id: str
    time_slot_id: str
    agent_id: str
    bid_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LimitOrderCreate(BaseModel):
    agent_id: str
    max_price: float


class LimitOrderResponse(BaseModel):
    id: str
    agent_id: str
    time_slot_id: str
    max_price: float
    status: str
    created_at: datetime
    executed_at: datetime | None = None
    bid_id: str | None = None

    model_config = {"from_attributes": True}
