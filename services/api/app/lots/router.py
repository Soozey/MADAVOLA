from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.common.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.core.config import settings
from app.db import get_db
from app.lots.schemas import LotConsolidate, LotCreate, LotOut, LotSplit, LotTransfer
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


@router.get("", response_model=PaginatedResponse[LotOut])
def list_lots(
    owner_actor_id: int | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(get_pagination),
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
    
    # Count total
    total = query.count()
    
    # Apply pagination
    lots = query.order_by(Lot.declared_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    
    items = [
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
    
    return PaginatedResponse.create(items, total, pagination.page, pagination.page_size)


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


@router.post("/consolidate", response_model=LotOut, status_code=201)
def consolidate_lots(
    payload: LotConsolidate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if len(payload.lot_ids) < 2:
        raise bad_request("lots_insuffisants")
    lots = db.query(Lot).filter(Lot.id.in_(payload.lot_ids)).all()
    if len(lots) != len(set(payload.lot_ids)):
        raise bad_request("lot_introuvable")
    for lot in lots:
        if lot.current_owner_actor_id != current_actor.id:
            raise bad_request("acces_refuse")
        if lot.status != "available":
            raise bad_request("lot_non_disponible")
    total = sum([float(lot.quantity) for lot in lots])
    parent = Lot(
        filiere=lots[0].filiere,
        product_type=payload.product_type,
        unit=payload.unit,
        quantity=total,
        declared_by_actor_id=current_actor.id,
        current_owner_actor_id=current_actor.id,
        status="available",
        declare_geo_point_id=payload.declare_geo_point_id,
    )
    db.add(parent)
    db.flush()
    for lot in lots:
        lot.parent_lot_id = parent.id
        lot.status = "consolidated"
        db.add(
            InventoryLedger(
                actor_id=current_actor.id,
                lot_id=lot.id,
                movement_type="consolidate_out",
                quantity_delta=-lot.quantity,
                ref_event_type="consolidation",
                ref_event_id=str(parent.id),
            )
        )
    db.add(
        InventoryLedger(
            actor_id=current_actor.id,
            lot_id=parent.id,
            movement_type="consolidate_in",
            quantity_delta=total,
            ref_event_type="consolidation",
            ref_event_id=str(parent.id),
        )
    )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="lot_consolidated",
        entity_type="lot",
        entity_id=str(parent.id),
        meta={"child_lot_ids": payload.lot_ids},
    )
    db.commit()
    db.refresh(parent)
    return LotOut(
        id=parent.id,
        filiere=parent.filiere,
        product_type=parent.product_type,
        unit=parent.unit,
        quantity=float(parent.quantity),
        declared_at=parent.declared_at,
        declared_by_actor_id=parent.declared_by_actor_id,
        current_owner_actor_id=parent.current_owner_actor_id,
        status=parent.status,
        declare_geo_point_id=parent.declare_geo_point_id,
    )


@router.post("/{lot_id}/split", response_model=list[LotOut])
def split_lot(
    lot_id: int,
    payload: LotSplit,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if lot.current_owner_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    if lot.status != "available":
        raise bad_request("lot_non_disponible")
    if not payload.quantities or sum(payload.quantities) != float(lot.quantity):
        raise bad_request("quantites_invalides")
    children = []
    for qty in payload.quantities:
        child = Lot(
            filiere=lot.filiere,
            product_type=lot.product_type,
            unit=lot.unit,
            quantity=qty,
            declared_by_actor_id=current_actor.id,
            current_owner_actor_id=current_actor.id,
            status="available",
            declare_geo_point_id=lot.declare_geo_point_id,
            parent_lot_id=lot.id,
        )
        db.add(child)
        db.flush()
        children.append(child)
        db.add(
            InventoryLedger(
                actor_id=current_actor.id,
                lot_id=child.id,
                movement_type="split_in",
                quantity_delta=qty,
                ref_event_type="split",
                ref_event_id=str(lot.id),
            )
        )
    lot.status = "split"
    db.add(
        InventoryLedger(
            actor_id=current_actor.id,
            lot_id=lot.id,
            movement_type="split_out",
            quantity_delta=-lot.quantity,
            ref_event_type="split",
            ref_event_id=str(lot.id),
        )
    )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="lot_split",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={"child_lot_ids": [c.id for c in children]},
    )
    db.commit()
    return [
        LotOut(
            id=child.id,
            filiere=child.filiere,
            product_type=child.product_type,
            unit=child.unit,
            quantity=float(child.quantity),
            declared_at=child.declared_at,
            declared_by_actor_id=child.declared_by_actor_id,
            current_owner_actor_id=child.current_owner_actor_id,
            status=child.status,
            declare_geo_point_id=child.declare_geo_point_id,
        )
        for child in children
    ]
