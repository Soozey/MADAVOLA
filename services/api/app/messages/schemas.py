from datetime import datetime

from pydantic import BaseModel


class ContactRequestCreate(BaseModel):
    target_actor_id: int


class ContactDecisionIn(BaseModel):
    decision: str  # accepted|rejected


class ContactRequestOut(BaseModel):
    id: int
    requester_actor_id: int
    target_actor_id: int
    status: str
    created_at: datetime
    decided_at: datetime | None = None
    requester_name: str | None = None
    target_name: str | None = None


class DirectMessageCreate(BaseModel):
    receiver_actor_id: int
    body: str


class DirectMessageOut(BaseModel):
    id: int
    contact_request_id: int | None = None
    sender_actor_id: int
    receiver_actor_id: int
    body: str
    created_at: datetime
    read_at: datetime | None = None
    sender_name: str | None = None
    receiver_name: str | None = None
