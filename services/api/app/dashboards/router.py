from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, get_actor_role_codes, require_permission
from app.auth.roles_config import (
    PERM_DASHBOARD_NATIONAL,
    PERM_DASHBOARD_REGIONAL,
    PERM_ALERTES_STRATEGIQUES,
    PERM_ADMIN_COMMUNE,
    has_permission,
)
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.export import ExportDossier
from app.models.lot import InventoryLedger
from app.models.territory import Region
from app.models.transaction import TradeTransaction
from app.dashboards.schemas import (
    DashboardNationalOut,
    DashboardRegionalOut,
    DashboardCommuneOut,
    AlerteItem,
)

router = APIRouter(prefix=f"{settings.api_prefix}/dashboards", tags=["dashboards"])


def _date_range(date_from: date | None, date_to: date | None) -> tuple[datetime, datetime]:
    if date_from and date_to and date_from > date_to:
        raise bad_request("intervalle_invalide")
    start = datetime.combine(date_from or date.today(), time.min, tzinfo=timezone.utc)
    end = datetime.combine(date_to or date.today(), time.max, tzinfo=timezone.utc)
    return start, end


@router.get("/national", response_model=DashboardNationalOut)
def dashboard_national(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor: Actor = Depends(require_permission(PERM_DASHBOARD_NATIONAL)),
):
    """Dashboard stratégique national : indicateurs agrégés et alertes. PR, PM, admin, dirigeant, MMRS, MEF, BFM, etc."""
    start_dt, end_dt = _date_range(date_from, date_to)

    volume_created = (
        db.query(func.coalesce(func.sum(InventoryLedger.quantity_delta), 0))
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    transactions_total = (
        db.query(func.coalesce(func.sum(TradeTransaction.total_amount), 0))
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )
    nb_acteurs = db.query(func.count(Actor.id)).filter(Actor.status == "active").scalar() or 0
    nb_lots = (
        db.query(func.count(func.distinct(InventoryLedger.lot_id)))
        .filter(InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    nb_exports_en_attente = (
        db.query(func.count(ExportDossier.id)).filter(ExportDossier.status == "submitted").scalar() or 0
    )

    alertes: list[AlerteItem] = []
    role_codes = get_actor_role_codes(current_actor, db)
    if has_permission(role_codes, PERM_ALERTES_STRATEGIQUES):
        # Placeholder : alertes stratégiques (à brancher sur règles métier réelles)
        alertes = [
            AlerteItem(
                id="a1",
                type="export",
                libelle="Vérifier les dossiers export en attente",
                severite="info",
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]

    return DashboardNationalOut(
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
        nb_acteurs=nb_acteurs,
        nb_lots=nb_lots,
        nb_exports_en_attente=nb_exports_en_attente,
        alertes_strategiques=alertes,
    )


@router.get("/regional", response_model=DashboardRegionalOut)
def dashboard_regional(
    region_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor: Actor = Depends(get_current_actor),
):
    """Dashboard régional : indicateurs par région. Gouverneur, admin, dirigeant (filtre par région si rôle region)."""
    role_codes = get_actor_role_codes(current_actor, db)
    if not has_permission(role_codes, PERM_DASHBOARD_REGIONAL) and "admin" not in role_codes and "dirigeant" not in role_codes:
        raise bad_request("acces_refuse")
    # Si rôle "region", limiter à sa région
    if "region" in role_codes and current_actor.region_id != region_id:
        raise bad_request("acces_refuse_region")
    if "commune_agent" in role_codes and current_actor.region_id != region_id:
        raise bad_request("acces_refuse_region")

    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise bad_request("region_introuvable")

    start_dt, end_dt = _date_range(date_from, date_to)

    volume_created = (
        db.query(func.coalesce(func.sum(InventoryLedger.quantity_delta), 0))
        .join(Actor, Actor.id == InventoryLedger.actor_id)
        .filter(Actor.region_id == region_id)
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    transactions_total = (
        db.query(func.coalesce(func.sum(TradeTransaction.total_amount), 0))
        .join(Actor, Actor.id == TradeTransaction.seller_actor_id)
        .filter(Actor.region_id == region_id)
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )
    nb_acteurs = db.query(func.count(Actor.id)).filter(Actor.region_id == region_id, Actor.status == "active").scalar() or 0
    nb_lots = (
        db.query(func.count(func.distinct(InventoryLedger.lot_id)))
        .join(Actor, Actor.id == InventoryLedger.actor_id)
        .filter(Actor.region_id == region_id)
        .filter(InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )

    return DashboardRegionalOut(
        region_id=region.id,
        region_code=region.code,
        region_name=region.name,
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
        nb_acteurs=nb_acteurs,
        nb_lots=nb_lots,
    )


@router.get("/commune", response_model=DashboardCommuneOut)
def dashboard_commune(
    commune_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_actor: Actor = Depends(get_current_actor),
):
    """Dashboard communal : indicateurs par commune. Agent commune (sa commune), admin, dirigeant."""
    from app.models.territory import Commune

    role_codes = get_actor_role_codes(current_actor, db)
    if not has_permission(role_codes, PERM_ADMIN_COMMUNE) and "admin" not in role_codes and "dirigeant" not in role_codes:
        raise bad_request("acces_refuse")
    if "commune_agent" in role_codes and current_actor.commune_id != commune_id:
        raise bad_request("acces_refuse_commune")

    commune = db.query(Commune).filter(Commune.id == commune_id).first()
    if not commune:
        raise bad_request("commune_introuvable")

    start_dt, end_dt = _date_range(date_from, date_to)

    volume_created = (
        db.query(func.coalesce(func.sum(InventoryLedger.quantity_delta), 0))
        .join(Actor, Actor.id == InventoryLedger.actor_id)
        .filter(Actor.commune_id == commune_id)
        .filter(InventoryLedger.movement_type == "create")
        .filter(InventoryLedger.created_at >= start_dt, InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )
    transactions_total = (
        db.query(func.coalesce(func.sum(TradeTransaction.total_amount), 0))
        .join(Actor, Actor.id == TradeTransaction.seller_actor_id)
        .filter(Actor.commune_id == commune_id)
        .filter(TradeTransaction.created_at >= start_dt, TradeTransaction.created_at <= end_dt)
        .scalar()
        or 0
    )
    nb_acteurs = db.query(func.count(Actor.id)).filter(Actor.commune_id == commune_id, Actor.status == "active").scalar() or 0
    nb_lots = (
        db.query(func.count(func.distinct(InventoryLedger.lot_id)))
        .join(Actor, Actor.id == InventoryLedger.actor_id)
        .filter(Actor.commune_id == commune_id)
        .filter(InventoryLedger.created_at <= end_dt)
        .scalar()
        or 0
    )

    return DashboardCommuneOut(
        commune_id=commune.id,
        commune_code=commune.code,
        commune_name=commune.name,
        volume_created=float(volume_created),
        transactions_total=float(transactions_total),
        nb_acteurs=nb_acteurs,
        nb_lots=nb_lots,
    )
