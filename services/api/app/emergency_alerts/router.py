from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.logger import write_audit
from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.emergency_alerts.schemas import (
    EmergencyAlertCreate,
    EmergencyAlertOut,
    EmergencyAlertStatusUpdate,
)
from app.models.actor import ActorRole
from app.models.emergency import EmergencyAlert

router = APIRouter(prefix=f"{settings.api_prefix}/emergency-alerts", tags=["emergency-alerts"])


CONTROL_ROLES = {
    "admin",
    "dirigeant",
    "police",
    "gendarmerie",
    "bianco",
    "forets",
    "environnement",
    "controleur",
    "bois_controleur",
    "pierre_controleur_mines",
}


def _has_any_role(db: Session, actor_id: int, roles: set[str]) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(roles), ActorRole.status == "active")
        .first()
        is not None
    )


@router.post("", response_model=EmergencyAlertOut, status_code=201)
def create_emergency_alert(
    payload: EmergencyAlertCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if payload.geo_point_id:
        # Basic existence check only; actor access control is handled in geo endpoint.
        from app.models.geo import GeoPoint

        geo = db.query(GeoPoint).filter_by(id=payload.geo_point_id).first()
        if not geo:
            raise bad_request("gps_introuvable")

    alert = EmergencyAlert(
        actor_id=current_actor.id,
        target_service=payload.target_service,
        filiere=(payload.filiere or "").upper() or None,
        role_code=payload.role_code,
        geo_point_id=payload.geo_point_id,
        title=payload.title.strip(),
        message=payload.message.strip(),
        severity=payload.severity,
        status="open",
    )
    db.add(alert)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="emergency_alert_created",
        entity_type="emergency_alert",
        entity_id=str(alert.id),
        meta={
            "target_service": alert.target_service,
            "severity": alert.severity,
            "filiere": alert.filiere,
        },
    )
    db.commit()
    db.refresh(alert)
    return EmergencyAlertOut.model_validate(alert)


@router.get("", response_model=list[EmergencyAlertOut])
def list_emergency_alerts(
    status: str | None = None,
    target_service: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(EmergencyAlert)
    can_control = _has_any_role(db, current_actor.id, CONTROL_ROLES)
    if not can_control:
        query = query.filter(EmergencyAlert.actor_id == current_actor.id)
    else:
        role_rows = (
            db.query(ActorRole.role)
            .filter(ActorRole.actor_id == current_actor.id, ActorRole.status == "active")
            .all()
        )
        role_codes = {row[0] for row in role_rows}
        if role_codes.isdisjoint({"admin", "dirigeant"}):
            allowed_targets = {"institutionnel"}
            if "police" in role_codes:
                allowed_targets.update({"police", "both"})
            if "gendarmerie" in role_codes:
                allowed_targets.update({"gendarmerie", "both"})
            if "bianco" in role_codes:
                allowed_targets.add("bianco")
            if "forets" in role_codes or "environnement" in role_codes:
                allowed_targets.add("environnement")
            query = query.filter(EmergencyAlert.target_service.in_(sorted(allowed_targets)))
    if status:
        query = query.filter(EmergencyAlert.status == status)
    if target_service:
        query = query.filter(EmergencyAlert.target_service == target_service)
    rows = query.order_by(EmergencyAlert.created_at.desc()).limit(300).all()
    return [EmergencyAlertOut.model_validate(row) for row in rows]


@router.patch("/{alert_id}/status", response_model=EmergencyAlertOut)
def update_emergency_alert_status(
    alert_id: int,
    payload: EmergencyAlertStatusUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _has_any_role(db, current_actor.id, CONTROL_ROLES):
        raise bad_request("acces_refuse")

    row = db.query(EmergencyAlert).filter_by(id=alert_id).first()
    if not row:
        raise bad_request("alerte_introuvable")

    row.status = payload.status
    row.handled_by_actor_id = current_actor.id
    now = datetime.now(timezone.utc)
    if payload.status == "acknowledged":
        row.acknowledged_at = now
    if payload.status in {"resolved", "rejected"}:
        row.resolved_at = now

    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=current_actor.id,
        action="emergency_alert_status_updated",
        entity_type="emergency_alert",
        entity_id=str(alert_id),
        meta={"status": payload.status},
    )
    return EmergencyAlertOut.model_validate(row)
