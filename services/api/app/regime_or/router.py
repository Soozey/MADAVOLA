from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.audit.logger import write_audit
from app.common.errors import bad_request, not_found
from app.common.receipts import build_qr_value
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.geo import GeoPoint
from app.models.gold_ops import (
    ExportChecklistItem,
    ExportValidation,
    ForexRepatriation,
    LegalVersioning,
    LotTestCertificate,
    TransformationEvent,
    TransformationFacility,
    TransportEvent,
)
from app.models.document import Document
from app.models.lot import InventoryLedger, Lot
from app.models.tax import TaxRecord
from app.regime_or.schemas import (
    ExportValidationCreate,
    ExportChecklistItemOut,
    ExportChecklistVerifyIn,
    ExportValidationOut,
    ForexRepatriationCreate,
    ForexRepatriationOut,
    LegalVersionCreate,
    LegalVersionOut,
    LotTestCertificateCreate,
    LotTestCertificateOut,
    TransformationEventCreate,
    TransformationEventOut,
    TransformationFacilityCreate,
    TransformationFacilityOut,
    TransportEventArrivalPatch,
    TransportEventCreate,
    TransportEventOut,
)

router = APIRouter(prefix=f"{settings.api_prefix}/or", tags=["regime_or"])


def _has_role(db: Session, actor_id: int, roles: set[str]) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(roles), ActorRole.status == "active")
        .first()
        is not None
    )


@router.post("/legal-versions", response_model=LegalVersionOut, status_code=201)
def create_legal_version(
    payload: LegalVersionCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "mef", "mmrs", "com"})),
):
    if payload.effective_to and payload.effective_to <= payload.effective_from:
        raise bad_request("periode_legale_invalide")
    if payload.status == "active":
        existing = (
            db.query(LegalVersioning)
            .filter(
                LegalVersioning.filiere == payload.filiere,
                LegalVersioning.legal_key == payload.legal_key,
                LegalVersioning.status == "active",
            )
            .all()
        )
        for row in existing:
            row.status = "inactive"

    version = LegalVersioning(
        filiere=payload.filiere,
        legal_key=payload.legal_key,
        version_tag=payload.version_tag,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        payload_json=payload.payload_json,
        status=payload.status,
        created_by_actor_id=current_actor.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return LegalVersionOut(
        id=version.id,
        filiere=version.filiere,
        legal_key=version.legal_key,
        version_tag=version.version_tag,
        effective_from=version.effective_from,
        effective_to=version.effective_to,
        payload_json=version.payload_json,
        status=version.status,
    )


@router.get("/legal-versions/active", response_model=LegalVersionOut)
def get_active_legal_version(
    filiere: str = Query("OR"),
    legal_key: str = Query("dtspm"),
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    now = datetime.now(timezone.utc)
    version = (
        db.query(LegalVersioning)
        .filter(
            LegalVersioning.filiere == filiere,
            LegalVersioning.legal_key == legal_key,
            LegalVersioning.status == "active",
            LegalVersioning.effective_from <= now,
        )
        .order_by(LegalVersioning.effective_from.desc())
        .first()
    )
    if not version:
        raise not_found("version_legale_introuvable")
    return LegalVersionOut(
        id=version.id,
        filiere=version.filiere,
        legal_key=version.legal_key,
        version_tag=version.version_tag,
        effective_from=version.effective_from,
        effective_to=version.effective_to,
        payload_json=version.payload_json,
        status=version.status,
    )


@router.post("/test-certificates", response_model=LotTestCertificateOut, status_code=201)
def create_test_certificate(
    payload: LotTestCertificateCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "centre_test", "analyse_certification", "com"})),
):
    lot = db.query(Lot).filter_by(id=payload.lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if not lot.qr_code:
        raise bad_request("scan_qr_obligatoire")

    sequence = db.query(LotTestCertificate).count() + 1
    cert = LotTestCertificate(
        lot_id=payload.lot_id,
        tested_by_actor_id=current_actor.id,
        gross_weight=payload.gross_weight,
        purity=payload.purity,
        certificate_number=f"CERT-OR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{sequence:06d}",
        certificate_qr=build_qr_value("test-certificate", str(payload.lot_id)),
        status="validated",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return _to_certificate_out(cert)


@router.post("/transport-events", response_model=TransportEventOut, status_code=201)
def create_transport_event(
    payload: TransportEventCreate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "transporteur_agree"})),
):
    lot = db.query(Lot).filter_by(id=payload.lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    depart_geo = db.query(GeoPoint).filter_by(id=payload.depart_geo_point_id).first()
    if not depart_geo:
        raise bad_request("gps_obligatoire")
    event = TransportEvent(
        lot_id=payload.lot_id,
        transporter_actor_id=payload.transporter_actor_id,
        depart_actor_id=payload.depart_actor_id,
        arrival_actor_id=payload.arrival_actor_id,
        depart_geo_point_id=payload.depart_geo_point_id,
        laissez_passer_document_id=payload.laissez_passer_document_id,
        status="in_transit",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_transport_out(event)


@router.patch("/transport-events/{event_id}/arrival", response_model=TransportEventOut)
def close_transport_event(
    event_id: int,
    payload: TransportEventArrivalPatch,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "transporteur_agree"})),
):
    event = db.query(TransportEvent).filter_by(id=event_id).first()
    if not event:
        raise not_found("transport_introuvable")
    arrival_geo = db.query(GeoPoint).filter_by(id=payload.arrival_geo_point_id).first()
    if not arrival_geo:
        raise bad_request("gps_obligatoire")
    event.arrival_geo_point_id = payload.arrival_geo_point_id
    event.arrival_at = datetime.now(timezone.utc)
    event.status = payload.status
    db.commit()
    db.refresh(event)
    return _to_transport_out(event)


@router.post("/transformation-facilities", response_model=TransformationFacilityOut, status_code=201)
def create_transformation_facility(
    payload: TransformationFacilityCreate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "mmrs", "com"})),
):
    facility = TransformationFacility(
        facility_type=payload.facility_type,
        operator_actor_id=payload.operator_actor_id,
        autorisation_ref=payload.autorisation_ref,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        capacity_declared=payload.capacity_declared,
        status=payload.status,
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return _to_facility_out(facility)


@router.post("/transformation-events", response_model=TransformationEventOut, status_code=201)
def create_transformation_event(
    payload: TransformationEventCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(
        require_roles({"admin", "dirigeant", "raffinerie_operator", "raffinerie_supervisor", "raffinerie_conformite"})
    ),
):
    facility = db.query(TransformationFacility).filter_by(id=payload.facility_id).first()
    if not facility:
        raise bad_request("installation_introuvable")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    valid_from = facility.valid_from.replace(tzinfo=None) if facility.valid_from.tzinfo else facility.valid_from
    valid_to = facility.valid_to.replace(tzinfo=None) if facility.valid_to.tzinfo else facility.valid_to
    if facility.status != "active" or not (valid_from <= now <= valid_to):
        raise bad_request("autorisation_transformation_invalide")
    if current_actor.id != facility.operator_actor_id and not _has_role(db, current_actor.id, {"admin", "dirigeant"}):
        raise bad_request("acces_refuse")

    lot = db.query(Lot).filter_by(id=payload.lot_input_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if float(payload.quantity_input) > float(lot.quantity):
        raise bad_request("quantite_superieure_stock")

    due_taxes = (
        db.query(TaxRecord.id)
        .filter(TaxRecord.lot_id == lot.id, TaxRecord.status == "DUE")
        .first()
    )
    if due_taxes:
        raise bad_request("taxes_amont_non_acquittees")

    expected = Decimal(str(payload.quantity_output)) + Decimal(str(payload.perte_declared))
    input_qty = Decimal(str(payload.quantity_input))
    if abs(expected - input_qty) > Decimal("0.0001"):
        raise bad_request("bilan_masse_invalide")
    if abs(expected - input_qty) > Decimal("0.01") and not payload.justificatif:
        raise bad_request("justificatif_obligatoire_ecart")

    output_lot = Lot(
        filiere=lot.filiere,
        product_type=payload.output_product_type,
        unit=payload.output_unit,
        quantity=payload.quantity_output,
        declared_by_actor_id=lot.declared_by_actor_id,
        current_owner_actor_id=lot.current_owner_actor_id,
        status="available",
        declare_geo_point_id=lot.declare_geo_point_id,
        parent_lot_id=lot.id,
        notes=f"Transformation depuis lot {lot.id}",
        qr_code=build_qr_value("lot", f"transform-{lot.id}-{datetime.now(timezone.utc).timestamp()}"),
    )
    db.add(output_lot)
    db.flush()

    event = TransformationEvent(
        lot_input_id=payload.lot_input_id,
        facility_id=payload.facility_id,
        quantity_input=payload.quantity_input,
        quantity_output=payload.quantity_output,
        perte_declared=payload.perte_declared,
        justificatif=payload.justificatif,
        validated_by_actor_id=current_actor.id,
        output_lot_id=output_lot.id,
        status="validated",
    )
    db.add(event)
    lot.status = "transformed"
    db.add(
        InventoryLedger(
            actor_id=lot.current_owner_actor_id,
            lot_id=lot.id,
            movement_type="transform_out",
            quantity_delta=-payload.quantity_input,
            ref_event_type="transformation",
            ref_event_id="pending",
        )
    )
    db.add(
        InventoryLedger(
            actor_id=output_lot.current_owner_actor_id,
            lot_id=output_lot.id,
            movement_type="transform_in",
            quantity_delta=payload.quantity_output,
            ref_event_type="transformation",
            ref_event_id="pending",
        )
    )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="transformation_event_created",
        entity_type="transformation_event",
        entity_id=str(event.id),
        meta={"lot_input_id": payload.lot_input_id, "output_lot_id": output_lot.id},
    )
    db.commit()
    db.refresh(event)
    return _to_transformation_out(event)


@router.post("/export-validations", response_model=ExportValidationOut, status_code=201)
def create_export_validation(
    payload: ExportValidationCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "dgd", "gue"})),
):
    if payload.validator_role not in {"com", "dgd", "gue"}:
        raise bad_request("role_validateur_invalide")
    validation = ExportValidation(
        export_id=payload.export_id,
        validator_actor_id=current_actor.id,
        validator_role=payload.validator_role,
        decision=payload.decision,
        notes=payload.notes,
    )
    db.add(validation)
    db.commit()
    db.refresh(validation)
    return _to_export_validation_out(validation)


@router.post("/forex-repatriations", response_model=ForexRepatriationOut, status_code=201)
def create_forex_repatriation(
    payload: ForexRepatriationCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "bfm", "banque_centrale", "banque_commerciale"})),
):
    rep = ForexRepatriation(
        export_id=payload.export_id,
        bank_actor_id=current_actor.id,
        proof_document_id=payload.proof_document_id,
        amount=payload.amount,
        currency=payload.currency,
        status=payload.status,
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return _to_forex_out(rep)


@router.get("/exports/{export_id}/checklist", response_model=list[ExportChecklistItemOut])
def list_export_checklist(
    export_id: int,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "com", "gue", "dgd", "comptoir_operator", "comptoir_compliance", "comptoir_director", "bijoutier"})),
):
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ExportChecklistItem)
        .filter(ExportChecklistItem.export_id == export_id)
        .order_by(ExportChecklistItem.id.asc())
        .all()
    )
    return [
        ExportChecklistItemOut(
            id=row.id,
            export_id=row.export_id,
            doc_type=row.doc_type,
            required=row.required,
            status=row.status,
            document_id=row.document_id,
            due_at=row.due_at,
            verified_by_actor_id=row.verified_by_actor_id,
            verified_at=row.verified_at,
            notes=row.notes,
            is_overdue=(
                row.status != "verified"
                and now > (row.due_at if row.due_at.tzinfo else row.due_at.replace(tzinfo=timezone.utc))
            ),
        )
        for row in rows
    ]


@router.post("/exports/{export_id}/checklist/verify", response_model=ExportChecklistItemOut)
def verify_export_checklist_item(
    export_id: int,
    payload: ExportChecklistVerifyIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "com", "gue", "dgd", "comptoir_compliance", "comptoir_director"})),
):
    item = (
        db.query(ExportChecklistItem)
        .filter(ExportChecklistItem.id == payload.checklist_item_id, ExportChecklistItem.export_id == export_id)
        .first()
    )
    if not item:
        raise not_found("checklist_piece_introuvable")
    doc = db.query(Document).filter(Document.id == payload.document_id).first()
    if not doc:
        raise not_found("document_introuvable")
    if doc.doc_type != item.doc_type:
        raise bad_request("document_type_incoherent")
    if doc.related_entity_type != "export" or doc.related_entity_id != str(export_id):
        raise bad_request("document_non_associe_export")

    item.document_id = doc.id
    item.status = "verified"
    item.verified_by_actor_id = current_actor.id
    item.verified_at = datetime.now(timezone.utc)
    item.notes = payload.notes
    db.commit()
    db.refresh(item)
    now = datetime.now(timezone.utc)
    return ExportChecklistItemOut(
        id=item.id,
        export_id=item.export_id,
        doc_type=item.doc_type,
        required=item.required,
        status=item.status,
        document_id=item.document_id,
        due_at=item.due_at,
        verified_by_actor_id=item.verified_by_actor_id,
        verified_at=item.verified_at,
        notes=item.notes,
        is_overdue=(
            item.status != "verified"
            and now > (item.due_at if item.due_at.tzinfo else item.due_at.replace(tzinfo=timezone.utc))
        ),
    )


def _to_certificate_out(row: LotTestCertificate) -> LotTestCertificateOut:
    return LotTestCertificateOut(
        id=row.id,
        lot_id=row.lot_id,
        tested_by_actor_id=row.tested_by_actor_id,
        gross_weight=float(row.gross_weight),
        purity=float(row.purity),
        certificate_number=row.certificate_number,
        certificate_qr=row.certificate_qr,
        status=row.status,
        issued_at=row.issued_at,
    )


def _to_transport_out(row: TransportEvent) -> TransportEventOut:
    return TransportEventOut(
        id=row.id,
        lot_id=row.lot_id,
        transporter_actor_id=row.transporter_actor_id,
        depart_actor_id=row.depart_actor_id,
        arrival_actor_id=row.arrival_actor_id,
        depart_geo_point_id=row.depart_geo_point_id,
        arrival_geo_point_id=row.arrival_geo_point_id,
        laissez_passer_document_id=row.laissez_passer_document_id,
        depart_at=row.depart_at,
        arrival_at=row.arrival_at,
        status=row.status,
    )


def _to_facility_out(row: TransformationFacility) -> TransformationFacilityOut:
    return TransformationFacilityOut(
        id=row.id,
        facility_type=row.facility_type,
        operator_actor_id=row.operator_actor_id,
        autorisation_ref=row.autorisation_ref,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        capacity_declared=float(row.capacity_declared) if row.capacity_declared is not None else None,
        status=row.status,
    )


def _to_transformation_out(row: TransformationEvent) -> TransformationEventOut:
    return TransformationEventOut(
        id=row.id,
        lot_input_id=row.lot_input_id,
        facility_id=row.facility_id,
        quantity_input=float(row.quantity_input),
        quantity_output=float(row.quantity_output),
        perte_declared=float(row.perte_declared),
        justificatif=row.justificatif,
        validated_by_actor_id=row.validated_by_actor_id,
        output_lot_id=row.output_lot_id,
        status=row.status,
        created_at=row.created_at,
    )


def _to_export_validation_out(row: ExportValidation) -> ExportValidationOut:
    return ExportValidationOut(
        id=row.id,
        export_id=row.export_id,
        validator_actor_id=row.validator_actor_id,
        validator_role=row.validator_role,
        decision=row.decision,
        notes=row.notes,
        created_at=row.created_at,
    )


def _to_forex_out(row: ForexRepatriation) -> ForexRepatriationOut:
    return ForexRepatriationOut(
        id=row.id,
        export_id=row.export_id,
        bank_actor_id=row.bank_actor_id,
        proof_document_id=row.proof_document_id,
        amount=float(row.amount),
        currency=row.currency,
        status=row.status,
        repatriated_at=row.repatriated_at,
    )
