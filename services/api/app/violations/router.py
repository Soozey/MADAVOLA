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
    )


def _is_inspector(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["controleur"]))
        .first()
        is not None
    )
