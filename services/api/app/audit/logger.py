import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str,
    justification: str | None = None,
    meta: dict | None = None,
) -> None:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        justification=justification,
        meta_json=json.dumps(meta, ensure_ascii=True) if meta else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
