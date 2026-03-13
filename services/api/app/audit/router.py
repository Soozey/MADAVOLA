from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.logger import write_audit
from app.auth.dependencies import get_current_actor, get_actor_role_codes
from app.auth.roles_config import has_permission, PERM_AUDIT_LOGS
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.audit import AuditLog
from app.models.lot import InventoryLedger, Lot
from app.audit.schemas import AuditLogOut, StockCoherenceItemOut, StockCoherenceReportOut

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


@router.get("/stock-coherence", response_model=StockCoherenceReportOut)
def audit_stock_coherence(
    actor_id: int | None = None,
    lot_id: int | None = None,
    include_coherent: bool = False,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _can_see_all_audit(db, current_actor):
        if actor_id and actor_id != current_actor.id:
            raise bad_request("acces_refuse")
        actor_id = current_actor.id

    query = db.query(Lot)
    if actor_id:
        query = query.filter(Lot.current_owner_actor_id == actor_id)
    if lot_id:
        query = query.filter(Lot.id == lot_id)

    lots = query.all()
    items: list[StockCoherenceItemOut] = []
    alerts_created = 0
    for row in lots:
        if row.status not in {"available", "available_for_sale", "suspect"}:
            continue
        ledger_qty = (
            db.query(func.sum(InventoryLedger.quantity_delta))
            .filter(InventoryLedger.lot_id == row.id, InventoryLedger.actor_id == row.current_owner_actor_id)
            .scalar()
        )
        ledger_val = float(ledger_qty or 0)
        declared_val = float(row.quantity or 0)
        delta = round(declared_val - ledger_val, 4)
        is_coherent = abs(delta) < 0.0001
        if include_coherent or not is_coherent:
            items.append(
                StockCoherenceItemOut(
                    lot_id=row.id,
                    actor_id=row.current_owner_actor_id,
                    lot_status=row.status,
                    declared_quantity=declared_val,
                    ledger_quantity=ledger_val,
                    delta=delta,
                    is_coherent=is_coherent,
                )
            )
        if not is_coherent:
            write_audit(
                db,
                actor_id=current_actor.id,
                action="stock_incoherence_alert",
                entity_type="lot",
                entity_id=str(row.id),
                meta={
                    "owner_actor_id": row.current_owner_actor_id,
                    "declared_quantity": declared_val,
                    "ledger_quantity": ledger_val,
                    "delta": delta,
                },
            )
            alerts_created += 1

    db.commit()
    incoherent_count = len([i for i in items if not i.is_coherent]) if include_coherent else len(items)
    return StockCoherenceReportOut(
        total_checked=len(lots),
        incoherent_count=incoherent_count,
        alerts_created=alerts_created,
        items=items,
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
