from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.or_compliance import ComplianceNotification
from app.models.pierre import ActorAuthorization

router = APIRouter(prefix=f"{settings.api_prefix}/notifications", tags=["notifications"])


def _make_notifications_for_authorizations(db: Session, thresholds: list[int], actor_id: int) -> int:
    now = datetime.now(timezone.utc)
    created = 0
    rows = db.query(ActorAuthorization).filter(ActorAuthorization.status == "active").all()
    for row in rows:
        valid_to = row.valid_to
        if valid_to.tzinfo is None:
            valid_to = valid_to.replace(tzinfo=timezone.utc)
        days_before = (valid_to.date() - now.date()).days
        if days_before not in thresholds:
            continue
        existing = (
            db.query(ComplianceNotification.id)
            .filter(
                ComplianceNotification.entity_type == "authorization",
                ComplianceNotification.entity_id == row.id,
                ComplianceNotification.actor_id == row.actor_id,
                ComplianceNotification.days_before == days_before,
            )
            .first()
        )
        if existing:
            continue
        db.add(
            ComplianceNotification(
                entity_type="authorization",
                entity_id=row.id,
                actor_id=row.actor_id,
                channel="in_app",
                days_before=days_before,
                message=f"Autorisation {row.numero} expire dans {days_before} jour(s)",
                status="sent",
            )
        )
        write_audit(
            db,
            actor_id=actor_id,
            action="authorization_expiry_reminder_sent",
            entity_type="authorization",
            entity_id=str(row.id),
            meta={"days_before": days_before},
        )
        created += 1
    return created


@router.get("")
def list_notifications(
    actor_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(ComplianceNotification)
    if actor_id:
        if actor_id != current_actor.id:
            raise bad_request("acces_refuse")
        query = query.filter(ComplianceNotification.actor_id == actor_id)
    else:
        query = query.filter(ComplianceNotification.actor_id == current_actor.id)
    rows = query.order_by(ComplianceNotification.sent_at.desc()).all()
    return [
        {
            "id": row.id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "actor_id": row.actor_id,
            "days_before": row.days_before,
            "message": row.message,
            "status": row.status,
            "sent_at": row.sent_at,
        }
        for row in rows
    ]


@router.post("/run-expiry-reminders")
def run_expiry_reminders(
    thresholds: str = "30,7,1",
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "pierre_admin_central", "com_admin"})),
):
    parsed = []
    for token in thresholds.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            raise bad_request("seuil_rappel_invalide")
        parsed.append(int(token))
    created = _make_notifications_for_authorizations(db, parsed or [30, 7, 1], current_actor.id)
    db.commit()
    return {"created_notifications": created}
