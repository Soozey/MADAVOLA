from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.ledger.schemas import LedgerBalanceOut, LedgerEntryOut
from app.models.actor import ActorRole
from app.models.lot import InventoryLedger

router = APIRouter(prefix=f"{settings.api_prefix}/ledger", tags=["lots"])


@router.get("", response_model=list[LedgerEntryOut])
def list_ledger(
    actor_id: int | None = None,
    lot_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(InventoryLedger)
    if not _is_admin(db, current_actor.id):
        query = query.filter(InventoryLedger.actor_id == current_actor.id)
        if actor_id and actor_id != current_actor.id:
            return []
    if actor_id:
        query = query.filter(InventoryLedger.actor_id == actor_id)
    if lot_id:
        query = query.filter(InventoryLedger.lot_id == lot_id)
    entries = query.order_by(InventoryLedger.created_at.desc()).all()
    return [
        LedgerEntryOut(
            id=e.id,
            actor_id=e.actor_id,
            lot_id=e.lot_id,
            movement_type=e.movement_type,
            quantity_delta=float(e.quantity_delta),
            ref_event_type=e.ref_event_type,
            ref_event_id=e.ref_event_id,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/balance", response_model=list[LedgerBalanceOut])
def ledger_balance(
    actor_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id):
        if actor_id and actor_id != current_actor.id:
            return []
        actor_id = current_actor.id
    query = (
        db.query(
            InventoryLedger.actor_id,
            InventoryLedger.lot_id,
            func.sum(InventoryLedger.quantity_delta).label("quantity"),
        )
        .group_by(InventoryLedger.actor_id, InventoryLedger.lot_id)
    )
    if actor_id:
        query = query.filter(InventoryLedger.actor_id == actor_id)
    results = query.all()
    return [
        LedgerBalanceOut(
            actor_id=r.actor_id,
            lot_id=r.lot_id,
            quantity=float(r.quantity or 0),
        )
        for r in results
    ]


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
