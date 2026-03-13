from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None = None
    action: str
    entity_type: str
    entity_id: str
    justification: str | None = None
    meta_json: str | None = None
    created_at: datetime


class StockCoherenceItemOut(BaseModel):
    lot_id: int
    actor_id: int
    lot_status: str
    declared_quantity: float
    ledger_quantity: float
    delta: float
    is_coherent: bool


class StockCoherenceReportOut(BaseModel):
    total_checked: int
    incoherent_count: int
    alerts_created: int
    items: list[StockCoherenceItemOut]
