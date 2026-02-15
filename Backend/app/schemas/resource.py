from datetime import datetime

from pydantic import BaseModel


class ResourceCreate(BaseModel):
    name: str
    resource_type: str = "room"
    location: str
    capacity: int = 1
    attributes: dict | None = None


class ResourceUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    attributes: dict | None = None
    is_active: bool | None = None


class ResourceResponse(BaseModel):
    id: str
    name: str
    resource_type: str
    location: str
    capacity: int
    attributes: dict | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TimeSlotResponse(BaseModel):
    id: str
    resource_id: str
    start_time: datetime
    end_time: datetime
    status: str
    booked_agent_ids: list[str] = []

    model_config = {"from_attributes": True}


class TimeSlotGenerateRequest(BaseModel):
    start_date: str  # ISO date, e.g. "2026-03-01"
    end_date: str    # ISO date, e.g. "2026-03-07"
    daily_start_hour: int = 8   # e.g. 8 for 8:00 AM
    daily_end_hour: int = 22    # e.g. 22 for 10:00 PM
