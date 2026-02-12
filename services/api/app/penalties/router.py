from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.lot import InventoryLedger, Lot
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
    if payload.action_on_lot in {"block", "seize"}:
        inspection = violation.inspection
        if not inspection or not inspection.inspected_lot_id:
            raise bad_request("lot_introuvable")
        lot = db.query(Lot).filter_by(id=inspection.inspected_lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable")
        if payload.action_on_lot == "block":
            lot.status = "blocked"
            violation.status = "sanctioned"
            violation.lot_action_status = "blocked"
        else:
            previous_owner = lot.current_owner_actor_id
            lot.current_owner_actor_id = payload.seized_to_actor_id or current_actor.id
            lot.status = "seized"
            violation.status = "sanctioned"
            violation.lot_action_status = "seized"
            db.add(
                InventoryLedger(
                    actor_id=previous_owner,
                    lot_id=lot.id,
                    movement_type="seizure_out",
                    quantity_delta=-lot.quantity,
                    ref_event_type="penalty",
                    ref_event_id=str(penalty.id),
                )
            )
            db.add(
                InventoryLedger(
                    actor_id=lot.current_owner_actor_id,
                    lot_id=lot.id,
                    movement_type="seizure_in",
                    quantity_delta=lot.quantity,
                    ref_event_type="penalty",
                    ref_event_id=str(penalty.id),
                )
            )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="penalty_created",
        entity_type="penalty",
        entity_id=str(penalty.id),
        meta={
            "violation_case_id": payload.violation_case_id,
            "action_on_lot": payload.action_on_lot,
            "seized_to_actor_id": payload.seized_to_actor_id,
        },
    )
    db.commit()
    db.refresh(penalty)
    return PenaltyOut(
        id=penalty.id,
        violation_case_id=penalty.violation_case_id,
        penalty_type=penalty.penalty_type,
        amount=float(penalty.amount) if penalty.amount is not None else None,
        status=penalty.status,
        action_on_lot=payload.action_on_lot,
    )


@router.get("", response_model=list[PenaltyOut])
def list_penalties(
    violation_case_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Penalty)
    if not _is_admin(db, current_actor.id) and not _is_inspector(db, current_actor.id):
        return []
    if violation_case_id is not None:
        query = query.filter(Penalty.violation_case_id == violation_case_id)
    penalties = query.order_by(Penalty.id.desc()).all()
    return [
        PenaltyOut(
            id=p.id,
            violation_case_id=p.violation_case_id,
            penalty_type=p.penalty_type,
            amount=float(p.amount) if p.amount is not None else None,
            status=p.status,
            action_on_lot=None,
        )
        for p in penalties
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
