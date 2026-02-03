from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.inspections.schemas import InspectionCreate, InspectionOut
from app.models.actor import ActorRole
from app.models.geo import GeoPoint
from app.models.penalty import Inspection

router = APIRouter(prefix=f"{settings.api_prefix}/inspections", tags=["inspections"])


@router.post("", response_model=InspectionOut, status_code=201)
def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_inspector(db, current_actor.id):
        raise bad_request("acces_refuse")
    if payload.geo_point_id:
        geo = db.query(GeoPoint).filter_by(id=payload.geo_point_id).first()
        if not geo:
            raise bad_request("gps_introuvable")
    inspection = Inspection(
        inspector_actor_id=current_actor.id,
        inspected_actor_id=payload.inspected_actor_id,
        inspected_lot_id=payload.inspected_lot_id,
        inspected_invoice_id=payload.inspected_invoice_id,
        result=payload.result,
        reason_code=payload.reason_code,
        notes=payload.notes,
        geo_point_id=payload.geo_point_id,
    )
    db.add(inspection)
    db.flush()
    write_audit(
        db,
        actor_id=current_actor.id,
        action="inspection_created",
        entity_type="inspection",
        entity_id=str(inspection.id),
        meta={"result": payload.result},
    )
    db.commit()
    db.refresh(inspection)
    return InspectionOut(
        id=inspection.id,
        inspector_actor_id=inspection.inspector_actor_id,
        inspected_actor_id=inspection.inspected_actor_id,
        inspected_lot_id=inspection.inspected_lot_id,
        inspected_invoice_id=inspection.inspected_invoice_id,
        result=inspection.result,
        reason_code=inspection.reason_code,
        notes=inspection.notes,
    )


@router.get("", response_model=list[InspectionOut])
def list_inspections(
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Inspection)
    if not _is_admin(db, current_actor.id):
        query = query.filter(Inspection.inspector_actor_id == current_actor.id)
    inspections = query.order_by(Inspection.created_at.desc()).all()
    return [
        InspectionOut(
            id=i.id,
            inspector_actor_id=i.inspector_actor_id,
            inspected_actor_id=i.inspected_actor_id,
            inspected_lot_id=i.inspected_lot_id,
            inspected_invoice_id=i.inspected_invoice_id,
            result=i.result,
            reason_code=i.reason_code,
            notes=i.notes,
        )
        for i in inspections
    ]


def _is_inspector(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["controleur"]))
        .first()
        is not None
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
