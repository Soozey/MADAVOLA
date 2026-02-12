from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.penalty import Inspection, ViolationCase
from app.violations.schemas import ViolationCreate, ViolationOut

router = APIRouter(prefix=f"{settings.api_prefix}/violations", tags=["inspections"])


@router.post("", response_model=ViolationOut, status_code=201)
def create_violation(
    payload: ViolationCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_inspector(db, current_actor.id):
        raise bad_request("acces_refuse")
    inspection = db.query(Inspection).filter_by(id=payload.inspection_id).first()
    if not inspection:
        raise bad_request("inspection_introuvable")
    violation = ViolationCase(
        inspection_id=payload.inspection_id,
        violation_type=payload.violation_type,
        legal_basis_ref=payload.legal_basis_ref,
        status="open",
    )
    db.add(violation)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="violation_created",
        entity_type="violation",
        entity_id=str(violation.id),
        meta={"inspection_id": payload.inspection_id},
    )
    db.commit()
    db.refresh(violation)
    return ViolationOut(
        id=violation.id,
        inspection_id=violation.inspection_id,
        violation_type=violation.violation_type,
        legal_basis_ref=violation.legal_basis_ref,
        status=violation.status,
        lot_action_status=violation.lot_action_status,
    )


@router.get("", response_model=list[ViolationOut])
def list_violations(
    inspection_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(ViolationCase)
    if not _is_admin(db, current_actor.id) and not _is_inspector(db, current_actor.id):
        return []
    if inspection_id is not None:
        query = query.filter(ViolationCase.inspection_id == inspection_id)
    violations = query.order_by(ViolationCase.id.desc()).all()
    return [
        ViolationOut(
            id=v.id,
            inspection_id=v.inspection_id,
            violation_type=v.violation_type,
            legal_basis_ref=v.legal_basis_ref,
            status=v.status,
            lot_action_status=v.lot_action_status,
        )
        for v in violations
    ]


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


def _is_inspector(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(
            ActorRole.actor_id == actor_id,
            ActorRole.role.in_(["controleur", "admin", "dirigeant", "mmrs", "dgd", "police", "gendarmerie", "forets"]),
        )
        .first()
        is not None
    )
