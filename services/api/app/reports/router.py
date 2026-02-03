from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.lot import InventoryLedger
from app.models.transaction import TradeTransaction
from app.reports.schemas import ActorReportOut, CommuneReportOut, NationalReportOut

router = APIRouter(prefix=f"{settings.api_prefix}/reports", tags=["reports"])


@router.get("/commune", response_model=CommuneReportOut)
def report_commune(
    commune_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id):
        if not _is_commune_agent(db, current_actor.id) or current_actor.commune_id != commune_id:
            raise bad_request("acces_refuse")
    start_dt, end_dt = _date_range(date_from, date_to)

    volume_created = (
        db.query(func.sum(InventoryLedger.quantity_delta))
        .join(Actor, Actor.id == InventoryLedger.actor_id)
        .filter(Actor.commune_id == commune_id)
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )

    transactions_total = (
        db.query(func.sum(TradeTransaction.total_amount))
        .join(Actor, Actor.id == TradeTransaction.seller_actor_id)
        .filter(Actor.commune_id == commune_id)
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )

    return CommuneReportOut(
        commune_id=commune_id,
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
    )


@router.get("/actor", response_model=ActorReportOut)
def report_actor(
    actor_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id) and current_actor.id != actor_id:
        raise bad_request("acces_refuse")
    start_dt, end_dt = _date_range(date_from, date_to)
    volume_created = (
        db.query(func.sum(InventoryLedger.quantity_delta))
        .filter(InventoryLedger.actor_id == actor_id)
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    transactions_total = (
        db.query(func.sum(TradeTransaction.total_amount))
        .filter(TradeTransaction.seller_actor_id == actor_id)
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )
    return ActorReportOut(
        actor_id=actor_id,
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
    )


@router.get("/national", response_model=NationalReportOut)
def report_national(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id):
        raise bad_request("acces_refuse")
    start_dt, end_dt = _date_range(date_from, date_to)
    volume_created = (
        db.query(func.sum(InventoryLedger.quantity_delta))
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    transactions_total = (
        db.query(func.sum(TradeTransaction.total_amount))
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )
    return NationalReportOut(
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
    )


def _date_range(date_from: date | None, date_to: date | None) -> tuple[datetime, datetime]:
    if date_from and date_to and date_from > date_to:
        raise bad_request("intervalle_invalide")
    start = datetime.combine(date_from or date.today(), time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to or date.today(), time.max, tzinfo=timezone.utc)
    return start, end


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


def _is_commune_agent(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == "commune_agent")
        .first()
        is not None
    )
