from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    token_balance: float = 0.0
    max_bookings: int = 10


class AgentResponse(BaseModel):
    id: str
    name: str
    token_balance: float
    is_active: bool
    max_bookings: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentPreferenceCreate(BaseModel):
    preference_type: str
    preference_value: str
    weight: float = 0.5


class AgentPreferenceResponse(BaseModel):
    id: str
    agent_id: str
    preference_type: str
    preference_value: str
    weight: float

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: str
    agent_id: str
    amount: float
    type: str
    reference_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkAgentCreate(BaseModel):
    count: int
    name_prefix: str = "Agent"
    initial_balance: float = 0.0
    max_bookings: int = 10
    generate_preferences: bool = True
