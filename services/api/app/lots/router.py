from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.lots.schemas import LotCreate, LotOut, LotTransfer
from app.models.actor import Actor
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
from app.models.payment import PaymentRequest

router = APIRouter(prefix=f"{settings.api_prefix}/lots", tags=["lots"])


@router.post("", response_model=LotOut, status_code=201)
def create_lot(
    payload: LotCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if current_actor.id != payload.declared_by_actor_id:
        raise bad_request("acces_refuse")
    geo = db.query(GeoPoint).filter_by(id=payload.declare_geo_point_id).first()
    if not geo:
        raise bad_request("gps_obligatoire")
    actor = db.query(Actor).filter_by(id=payload.declared_by_actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")
    lot = Lot(
        filiere=payload.filiere,
        product_type=payload.product_type,
        unit=payload.unit,
        quantity=payload.quantity,
        declared_by_actor_id=payload.declared_by_actor_id,
        current_owner_actor_id=payload.declared_by_actor_id,
        status="available",
        declare_geo_point_id=payload.declare_geo_point_id,
    )
    db.add(lot)
    db.flush()
    db.add(
        InventoryLedger(
            actor_id=payload.declared_by_actor_id,
            lot_id=lot.id,
            movement_type="create",
            quantity_delta=payload.quantity,
            ref_event_type="lot",
            ref_event_id=str(lot.id),
        )
    )
    write_audit(
        db,
        actor_id=payload.declared_by_actor_id,
        action="lot_created",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={"quantity": str(payload.quantity), "unit": payload.unit},
    )
    db.commit()
    db.refresh(lot)
    return LotOut(
        id=lot.id,
        filiere=lot.filiere,
        product_type=lot.product_type,
        unit=lot.unit,
        quantity=float(lot.quantity),
        declared_at=lot.declared_at,
        declared_by_actor_id=lot.declared_by_actor_id,
        current_owner_actor_id=lot.current_owner_actor_id,
        status=lot.status,
        declare_geo_point_id=lot.declare_geo_point_id,
    )


@router.get("", response_model=list[LotOut])
def list_lots(
    owner_actor_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Lot)
    if owner_actor_id:
        if owner_actor_id != current_actor.id:
            raise bad_request("acces_refuse")
        query = query.filter(Lot.current_owner_actor_id == owner_actor_id)
    else:
        query = query.filter(Lot.current_owner_actor_id == current_actor.id)
    if status:
        query = query.filter(Lot.status == status)
    lots = query.order_by(Lot.declared_at.desc()).all()
    return [
        LotOut(
            id=lot.id,
            filiere=lot.filiere,
            product_type=lot.product_type,
            unit=lot.unit,
            quantity=float(lot.quantity),
            declared_at=lot.declared_at,
            declared_by_actor_id=lot.declared_by_actor_id,
            current_owner_actor_id=lot.current_owner_actor_id,
            status=lot.status,
            declare_geo_point_id=lot.declare_geo_point_id,
        )
        for lot in lots
    ]


@router.get("/{lot_id}", response_model=LotOut)
def get_lot(
    lot_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if lot.current_owner_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    return LotOut(
        id=lot.id,
        filiere=lot.filiere,
        product_type=lot.product_type,
        unit=lot.unit,
        quantity=float(lot.quantity),
        declared_at=lot.declared_at,
        declared_by_actor_id=lot.declared_by_actor_id,
        current_owner_actor_id=lot.current_owner_actor_id,
        status=lot.status,
        declare_geo_point_id=lot.declare_geo_point_id,
    )


@router.post("/{lot_id}/transfer", response_model=LotOut)
def transfer_lot(
    lot_id: int,
    payload: LotTransfer,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if lot.current_owner_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    payment = db.query(PaymentRequest).filter_by(id=payload.payment_request_id).first()
    if not payment or payment.status != "success":
        raise bad_request("paiement_requis")
    if payment.payer_actor_id != payload.new_owner_actor_id:
        raise bad_request("paiement_requis")
    new_owner = db.query(Actor).filter_by(id=payload.new_owner_actor_id).first()
    if not new_owner:
        raise bad_request("acteur_invalide")

    lot.current_owner_actor_id = payload.new_owner_actor_id
    lot.status = "available"
    db.add(
        InventoryLedger(
            actor_id=current_actor.id,
            lot_id=lot.id,
            movement_type="transfer_out",
            quantity_delta=-lot.quantity,
            ref_event_type="transfer",
            ref_event_id=str(payment.id),
        )
    )
    db.add(
        InventoryLedger(
            actor_id=new_owner.id,
            lot_id=lot.id,
            movement_type="transfer_in",
            quantity_delta=lot.quantity,
            ref_event_type="transfer",
            ref_event_id=str(payment.id),
        )
    )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="lot_transferred",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={"new_owner": new_owner.id, "payment_request_id": payment.id},
    )
    db.commit()
    db.refresh(lot)
    return LotOut(
        id=lot.id,
        filiere=lot.filiere,
        product_type=lot.product_type,
        unit=lot.unit,
        quantity=float(lot.quantity),
        declared_at=lot.declared_at,
        declared_by_actor_id=lot.declared_by_actor_id,
        current_owner_actor_id=lot.current_owner_actor_id,
        status=lot.status,
        declare_geo_point_id=lot.declare_geo_point_id,
    )
