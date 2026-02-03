from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.penalty import Penalty, ViolationCase
from app.penalties.schemas import PenaltyCreate, PenaltyOut

router = APIRouter(prefix=f"{settings.api_prefix}/penalties", tags=["inspections"])


@router.post("", response_model=PenaltyOut, status_code=201)
def create_penalty(
    payload: PenaltyCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_inspector(db, current_actor.id):
        raise bad_request("acces_refuse")
    violation = db.query(ViolationCase).filter_by(id=payload.violation_case_id).first()
    if not violation:
        raise bad_request("violation_introuvable")
    penalty = Penalty(
        violation_case_id=payload.violation_case_id,
        penalty_type=payload.penalty_type,
        amount=payload.amount,
        status="open",
        executed_by_actor_id=current_actor.id,
    )
    db.add(penalty)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="penalty_created",
        entity_type="penalty",
        entity_id=str(penalty.id),
        meta={"violation_case_id": payload.violation_case_id},
    )
    db.commit()
    db.refresh(penalty)
    return PenaltyOut(
        id=penalty.id,
        violation_case_id=penalty.violation_case_id,
        penalty_type=penalty.penalty_type,
        amount=float(penalty.amount) if penalty.amount is not None else None,
        status=penalty.status,
    )


def _is_inspector(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["controleur"]))
        .first()
        is not None
    )
