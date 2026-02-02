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
