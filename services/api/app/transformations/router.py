from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.common.errors import bad_request
from app.common.receipts import build_qr_value
from app.core.config import settings
from app.db import get_db
from app.models.gold_ops import TransformationEvent, TransformationFacility
from app.models.lot import InventoryLedger, Lot, LotLink


class TransformationOutputIn(BaseModel):
    quantity: float = Field(gt=0)
    unit: str
    wood_form: str


class TransformationCreateIn(BaseModel):
    operation_type: str
    facility_id: int | None = None
    input_lot_ids: list[int]
    outputs: list[TransformationOutputIn]
    notes: str | None = None


router = APIRouter(prefix=f"{settings.api_prefix}/transformations", tags=["transformations"])


@router.post("", status_code=201)
def create_transformation(
    payload: TransformationCreateIn,
    db: Session = Depends(get_db),
    actor=Depends(require_roles({"admin", "dirigeant", "bois_transformateur", "bois_artisan", "forets"})),
):
    if not payload.input_lot_ids or not payload.outputs:
        raise bad_request("transformation_invalide")
    inputs = db.query(Lot).filter(Lot.id.in_(payload.input_lot_ids)).all()
    if len(inputs) != len(set(payload.input_lot_ids)):
        raise bad_request("lot_introuvable")
    input_total = 0.0
    for lot in inputs:
        if lot.filiere != "BOIS":
            raise bad_request("lot_filiere_invalide")
        if lot.current_owner_actor_id != actor.id:
            raise bad_request("acces_refuse")
        if lot.status != "available":
            raise bad_request("lot_non_disponible")
        input_total += float(lot.quantity)

    output_total = sum([float(o.quantity) for o in payload.outputs])
    if output_total - input_total > 0.0001:
        raise bad_request("conservation_masse_invalide")

    loss_ratio = max(0.0, (input_total - output_total) / input_total) if input_total > 0 else 0
    event = TransformationEvent(
        lot_input_id=inputs[0].id,
        facility_id=payload.facility_id or 0,
        quantity_input=input_total,
        quantity_output=output_total,
        perte_declared=max(0.0, input_total - output_total),
        justificatif=payload.notes,
        validated_by_actor_id=actor.id,
        status="validated",
    )
    if not payload.facility_id:
        facility = (
            db.query(TransformationFacility)
            .filter(
                TransformationFacility.operator_actor_id == actor.id,
                TransformationFacility.facility_type == "atelier_bois",
                TransformationFacility.status == "active",
            )
            .first()
        )
        if not facility:
            facility = TransformationFacility(
                facility_type="atelier_bois",
                operator_actor_id=actor.id,
                autorisation_ref="AUTO-ATELIER-BOIS",
                valid_from=datetime.now(timezone.utc) - timedelta(days=1),
                valid_to=datetime.now(timezone.utc) + timedelta(days=365),
                status="active",
            )
            db.add(facility)
            db.flush()
        event.facility_id = facility.id
    db.add(event)
    db.flush()

    for lot in inputs:
        db.add(
            InventoryLedger(
                actor_id=actor.id,
                lot_id=lot.id,
                movement_type="transform_out",
                quantity_delta=-float(lot.quantity),
                ref_event_type="transformation",
                ref_event_id=str(event.id),
            )
        )
        lot.status = "transformed"

    output_lots = []
    first = inputs[0]
    for idx, out in enumerate(payload.outputs, start=1):
        child = Lot(
            filiere="BOIS",
            wood_essence_id=first.wood_essence_id,
            wood_form=out.wood_form,
            volume_m3=out.quantity if out.unit == "m3" else None,
            attributes_json=first.attributes_json,
            product_type=first.product_type,
            unit=out.unit,
            quantity=out.quantity,
            declared_by_actor_id=actor.id,
            current_owner_actor_id=actor.id,
            status="available",
            declare_geo_point_id=first.declare_geo_point_id,
            notes=payload.notes,
            photo_urls_json=first.photo_urls_json,
            qr_code=build_qr_value("lot", f"wood-transform-{event.id}-{idx}"),
        )
        db.add(child)
        db.flush()
        output_lots.append(child)
        db.add(
            LotLink(
                parent_lot_id=first.id,
                child_lot_id=child.id,
                relation_type="transformation",
                quantity_from_child=out.quantity,
            )
        )
        db.add(
            InventoryLedger(
                actor_id=actor.id,
                lot_id=child.id,
                movement_type="transform_in",
                quantity_delta=out.quantity,
                ref_event_type="transformation",
                ref_event_id=str(event.id),
            )
        )
    if output_lots:
        event.output_lot_id = output_lots[0].id

    db.commit()
    return {
        "event_id": event.id,
        "status": "completed",
        "input_lot_ids": payload.input_lot_ids,
        "output_lot_ids": [x.id for x in output_lots],
        "loss_ratio": float(loss_ratio),
        "created_at": datetime.now(timezone.utc),
    }
