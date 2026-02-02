from datetime import datetime

from pydantic import BaseModel


class LedgerEntryOut(BaseModel):
    id: int
    actor_id: int
    lot_id: int
    movement_type: str
    quantity_delta: float
    ref_event_type: str
    ref_event_id: str
    created_at: datetime


class LedgerBalanceOut(BaseModel):
    actor_id: int
    lot_id: int
    quantity: float
