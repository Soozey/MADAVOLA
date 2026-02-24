from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.common.errors import bad_request
from app.common.receipts import build_qr_value
from app.core.config import settings
from app.db import get_db
from app.models.lot import Lot
from app.models.bois import TransportRecord, TransportRecordItem
from app.models.territory import Commune, TerritoryVersion


class TransportItemIn(BaseModel):
    lot_id: int
    quantity: float = Field(gt=0)


class TransportCreateIn(BaseModel):
    transporter_actor_id: int
    origin: str
    destination: str
    vehicle_ref: str | None = None
    depart_at: datetime
    arrivee_estimee_at: datetime | None = None
    notes: str | None = None
    items: list[TransportItemIn]


class TransportOut(BaseModel):
    id: int
    transporter_actor_id: int
    origin: str
    destination: str
    status: str
    qr_code: str | None


class ScanVerifyIn(BaseModel):
    lot_id: int


router = APIRouter(prefix=f"{settings.api_prefix}/transports", tags=["transports"])


@router.post("", response_model=TransportOut, status_code=201)
def create_transport(
    payload: TransportCreateIn,
    db: Session = Depends(get_db),
    actor=Depends(require_roles({"admin", "dirigeant", "transporteur", "transporteur_agree", "bois_transporteur", "forets"})),
):
    if not payload.items:
        raise bad_request("items_obligatoires")
    active_version = db.query(TerritoryVersion).filter_by(status="active").first()
    if not active_version:
        raise bad_request("territoire_non_charge")
    origin_commune_code = _normalize_commune_code(payload.origin)
    destination_commune_code = _normalize_commune_code(payload.destination)
    origin_commune = (
        db.query(Commune)
        .filter(Commune.version_id == active_version.id, Commune.code == origin_commune_code)
        .first()
    )
    destination_commune = (
        db.query(Commune)
        .filter(Commune.version_id == active_version.id, Commune.code == destination_commune_code)
        .first()
    )
    if not origin_commune or not destination_commune:
        raise bad_request(
            "territoire_invalide",
            {
                "origin": payload.origin,
                "destination": payload.destination,
            },
        )

    record = TransportRecord(
        filiere="BOIS",
        transporter_actor_id=payload.transporter_actor_id,
        origin=origin_commune.code,
        destination=destination_commune.code,
        vehicle_ref=(payload.vehicle_ref or "").strip() or None,
        depart_at=payload.depart_at,
        arrivee_estimee_at=payload.arrivee_estimee_at,
        status="planned",
        notes=payload.notes,
        created_by_actor_id=actor.id,
    )
    db.add(record)
    db.flush()
    for item in payload.items:
        lot = db.query(Lot).filter_by(id=item.lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable", {"lot_id": item.lot_id})
        if lot.filiere != "BOIS":
            raise bad_request("lot_filiere_invalide", {"lot_id": item.lot_id})
        if float(item.quantity) > float(lot.quantity):
            raise bad_request("quantite_superieure_stock")
        db.add(
            TransportRecordItem(
                transport_record_id=record.id,
                lot_id=item.lot_id,
                quantity=item.quantity,
            )
        )
    record.qr_code = build_qr_value("transport", str(record.id))
    db.commit()
    db.refresh(record)
    return TransportOut(
        id=record.id,
        transporter_actor_id=record.transporter_actor_id,
        origin=record.origin,
        destination=record.destination,
        status=record.status,
        qr_code=record.qr_code,
    )


@router.post("/{transport_id}/scan_verify")
def scan_verify(
    transport_id: int,
    payload: ScanVerifyIn,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "controleur", "police", "gendarmerie", "bois_controleur", "bois_douanes"})),
):
    record = db.query(TransportRecord).filter_by(id=transport_id).first()
    if not record:
        raise bad_request("transport_introuvable")
    lot = db.query(Lot).filter_by(id=payload.lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    linked = (
        db.query(TransportRecordItem.id)
        .filter(TransportRecordItem.transport_record_id == transport_id, TransportRecordItem.lot_id == payload.lot_id)
        .first()
    )
    if not linked:
        return {
            "transport_id": transport_id,
            "lot_id": payload.lot_id,
            "result": "suspect",
            "reason": "lot_not_listed_in_transport",
            "verified_at": datetime.now(timezone.utc),
        }
    return {
        "transport_id": transport_id,
        "lot_id": payload.lot_id,
        "result": "ok",
        "owner_actor_id": lot.current_owner_actor_id,
        "lot_status": lot.status,
        "verified_at": datetime.now(timezone.utc),
    }


def _normalize_commune_code(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    return raw.split(" - ", 1)[0].strip()
