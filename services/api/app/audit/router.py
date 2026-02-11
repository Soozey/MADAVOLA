from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, get_actor_role_codes
from app.auth.roles_config import has_permission, PERM_AUDIT_LOGS
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.audit import AuditLog
from app.audit.schemas import AuditLogOut

router = APIRouter(prefix=f"{settings.api_prefix}/audit", tags=["admin"])


def _can_see_all_audit(db, actor) -> bool:
    if _is_admin(db, actor.id):
        return True
    role_codes = get_actor_role_codes(actor, db)
    return has_permission(role_codes, PERM_AUDIT_LOGS)  # BIANCO, Justice (réquisition à part)


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    actor_id: int | None = None,
    entity_type: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(AuditLog)
    if not _can_see_all_audit(db, current_actor):
        query = query.filter(AuditLog.actor_id == current_actor.id)
        if actor_id and actor_id != current_actor.id:
            return []
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    logs = query.order_by(AuditLog.created_at.desc()).all()
    return [
        AuditLogOut(
            id=log.id,
            actor_id=log.actor_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            justification=log.justification,
            meta_json=log.meta_json,
            created_at=log.created_at,
        )
        for log in logs
    ]


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
