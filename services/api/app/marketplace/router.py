from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.marketplace.schemas import MarketplaceOfferCreate, MarketplaceOfferOut
from app.models.actor import Actor, ActorRole
from app.models.lot import Lot
from app.models.marketplace import MarketplaceOffer

router = APIRouter(prefix=f"{settings.api_prefix}/marketplace/offers", tags=["marketplace"])


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole.id)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]), ActorRole.status == "active")
        .first()
        is not None
    )


def _offer_out(db: Session, row: MarketplaceOffer) -> MarketplaceOfferOut:
    actor = db.query(Actor).filter(Actor.id == row.actor_id).first()
    return MarketplaceOfferOut(
        id=row.id,
        actor_id=row.actor_id,
        actor_name=f"{actor.nom} {actor.prenoms or ''}".strip() if actor else None,
        offer_type=row.offer_type,
        filiere=row.filiere,
        lot_id=row.lot_id,
        product_type=row.product_type,
        quantity=float(row.quantity),
        unit=row.unit,
        unit_price=float(row.unit_price),
        currency=row.currency,
        location_commune_id=row.location_commune_id,
        status=row.status,
        expires_at=row.expires_at,
        notes=row.notes,
        created_at=row.created_at,
    )


@router.post("", response_model=MarketplaceOfferOut, status_code=201)
def create_offer(
    payload: MarketplaceOfferCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    offer_type = (payload.offer_type or "").strip().lower()
    if offer_type not in {"sell", "buy"}:
        raise bad_request("offre_invalide")
    lot_id = payload.lot_id
    filiere = (payload.filiere or "").strip().upper()
    product_type = (payload.product_type or "").strip()
    unit = (payload.unit or "").strip()
    if not filiere or not product_type or not unit:
        raise bad_request("offre_invalide")

    if offer_type == "sell":
        if not lot_id:
            raise bad_request("lot_obligatoire")
        lot = db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable")
        if lot.current_owner_actor_id != current_actor.id:
            raise bad_request("acces_refuse")
        if payload.quantity > float(lot.quantity):
            raise bad_request("quantite_superieure_stock")
        filiere = (lot.filiere or filiere).upper()
        product_type = lot.product_type or product_type
        unit = lot.unit or unit

    row = MarketplaceOffer(
        actor_id=current_actor.id,
        offer_type=offer_type,
        filiere=filiere,
        lot_id=lot_id,
        product_type=product_type,
        quantity=payload.quantity,
        unit=unit,
        unit_price=payload.unit_price,
        currency=(payload.currency or "MGA").upper(),
        location_commune_id=payload.location_commune_id or current_actor.commune_id,
        status="active",
        expires_at=payload.expires_at or (datetime.now(timezone.utc) + timedelta(days=7)),
        notes=(payload.notes or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _offer_out(db, row)


@router.get("", response_model=list[MarketplaceOfferOut])
def list_offers(
    offer_type: str | None = None,
    filiere: str | None = None,
    commune_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_quantity: float | None = None,
    max_quantity: float | None = None,
    status: str | None = "active",
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(MarketplaceOffer)
    if status:
        query = query.filter(MarketplaceOffer.status == status)
    if offer_type:
        query = query.filter(MarketplaceOffer.offer_type == offer_type.lower())
    if filiere:
        query = query.filter(MarketplaceOffer.filiere == filiere.upper())
    if commune_id:
        query = query.filter(MarketplaceOffer.location_commune_id == commune_id)
    if min_price is not None:
        query = query.filter(MarketplaceOffer.unit_price >= min_price)
    if max_price is not None:
        query = query.filter(MarketplaceOffer.unit_price <= max_price)
    if min_quantity is not None:
        query = query.filter(MarketplaceOffer.quantity >= min_quantity)
    if max_quantity is not None:
        query = query.filter(MarketplaceOffer.quantity <= max_quantity)
    if not _is_admin(db, current_actor.id) and status and status != "active":
        query = query.filter(MarketplaceOffer.actor_id == current_actor.id)
    rows = query.order_by(MarketplaceOffer.created_at.desc()).limit(500).all()
    return [_offer_out(db, row) for row in rows]


@router.post("/{offer_id}/close", response_model=MarketplaceOfferOut)
def close_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    row = db.query(MarketplaceOffer).filter(MarketplaceOffer.id == offer_id).first()
    if not row:
        raise bad_request("offre_introuvable")
    if row.actor_id != current_actor.id and not _is_admin(db, current_actor.id):
        raise bad_request("acces_refuse")
    row.status = "closed"
    db.commit()
    db.refresh(row)
    return _offer_out(db, row)
