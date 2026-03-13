from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.logger import write_audit
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
from app.models.admin import SystemConfig
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
    HomeWidgetsOut,
    InstitutionalMessageIn,
)

router = APIRouter(prefix=f"{settings.api_prefix}/dashboards", tags=["dashboards"])


def _get_config(db: Session, key: str) -> SystemConfig | None:
    return db.query(SystemConfig).filter(SystemConfig.key == key).first()


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


@router.get("/home-widgets", response_model=HomeWidgetsOut)
def home_widgets(
    db: Session = Depends(get_db),
    _current_actor: Actor = Depends(get_current_actor),
):
    price_row = _get_config(db, "gold_price_value")
    source_row = _get_config(db, "gold_price_source")
    currency_row = _get_config(db, "gold_price_currency")
    unit_row = _get_config(db, "gold_price_unit")
    message_row = _get_config(db, "institutional_message")
    message_version_row = _get_config(db, "institutional_message_version")
    price_value = None
    if price_row and (price_row.value or "").strip():
        try:
            price_value = float(price_row.value)
        except Exception:
            price_value = None
    message_version = None
    if message_version_row and (message_version_row.value or "").strip():
        try:
            message_version = int(message_version_row.value)
        except Exception:
            message_version = None
    return HomeWidgetsOut(
        gold_price_value=price_value,
        gold_price_currency=(currency_row.value if currency_row and currency_row.value else "MGA"),
        gold_price_unit=(unit_row.value if unit_row and unit_row.value else "g"),
        gold_price_source=source_row.value if source_row else None,
        gold_price_updated_at=price_row.updated_at.isoformat() if price_row and price_row.updated_at else None,
        institutional_message=message_row.value if message_row else None,
        institutional_message_version=message_version,
        institutional_message_updated_at=message_row.updated_at.isoformat() if message_row and message_row.updated_at else None,
    )


@router.post("/institutional-message", response_model=HomeWidgetsOut)
def publish_institutional_message(
    payload: InstitutionalMessageIn,
    db: Session = Depends(get_db),
    current_actor: Actor = Depends(get_current_actor),
):
    role_codes = get_actor_role_codes(current_actor, db)
    if set(role_codes).isdisjoint({"admin", "dirigeant", "president", "pr"}):
        raise bad_request("acces_refuse")
    message_text = (payload.message or "").strip()
    if not message_text:
        raise bad_request("message_obligatoire")
    now = datetime.now(timezone.utc)
    message_row = _get_config(db, "institutional_message")
    if not message_row:
        message_row = SystemConfig(
            key="institutional_message",
            value=message_text,
            description="Message institutionnel affiche a l'accueil",
            updated_by_actor_id=current_actor.id,
            updated_at=now,
        )
        db.add(message_row)
    else:
        message_row.value = message_text
        message_row.updated_by_actor_id = current_actor.id
        message_row.updated_at = now
    version_row = _get_config(db, "institutional_message_version")
    if not version_row:
        version_row = SystemConfig(
            key="institutional_message_version",
            value="1",
            description="Version du message institutionnel",
            updated_by_actor_id=current_actor.id,
            updated_at=now,
        )
        db.add(version_row)
    else:
        try:
            current_version = int(version_row.value or "0")
        except Exception:
            current_version = 0
        version_row.value = str(current_version + 1)
        version_row.updated_by_actor_id = current_actor.id
        version_row.updated_at = now
    db.commit()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="institutional_message_published",
        entity_type="system_config",
        entity_id="institutional_message",
        meta={"length": len(message_text)},
    )
    db.commit()
    return home_widgets(db=db, _current_actor=current_actor)
