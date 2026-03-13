import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.common.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.common.receipts import build_receipt_number, build_simple_pdf
from app.common.traceability import build_lot_number, build_traceability_id, canonical_json, compute_chain_hash
from app.core.config import settings
from app.db import get_db
from app.lots.schemas import LotConsolidate, LotCreate, LotOut, LotSplit, LotTransfer, LotWoodClassificationPatch
from app.models.actor import Actor
from app.models.actor import ActorRole
from app.models.document import Document
from app.models.geo import GeoPoint
from app.models.gold_ops import TransportEvent
from app.models.lot import InventoryLedger, Lot
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.payment import PaymentRequest
from app.models.territory import Region
from app.or_compliance.rules import can_declare_or_lot, can_trade_or
from app.models.pierre import ActorAuthorization, ProductCatalog
from app.models.bois import ChecklistPolicy, EssenceCatalog

router = APIRouter(prefix=f"{settings.api_prefix}/lots", tags=["lots"])

WOOD_CLASSIFICATIONS = {
    "LEGAL_EXPORTABLE",
    "LEGAL_NON_EXPORTABLE",
    "ILLEGAL",
    "A_DETRUIRE",
}
CITES_STATUSES = {"not_required", "required", "pending", "approved", "rejected"}
DESTRUCTION_STATUSES = {"pending", "approved", "validated", "rejected", "destroyed"}


def _active_roles(db: Session, actor_id: int) -> set[str]:
    rows = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    return {row[0] for row in rows}


def _ensure_active_authorization(db: Session, actor_id: int, filiere: str) -> None:
    now = lot_now()
    auth = (
        db.query(ActorAuthorization.id)
        .filter(
            ActorAuthorization.actor_id == actor_id,
            ActorAuthorization.filiere == filiere,
            ActorAuthorization.status == "active",
            ActorAuthorization.valid_from <= now,
            ActorAuthorization.valid_to >= now,
        )
        .first()
    )
    if not auth:
        raise bad_request("autorisation_expiree")


def _check_required_docs(
    db: Session,
    actor_id: int,
    filiere: str,
    operation: str,
    category: str | None,
    document_ids: list[int],
) -> None:
    policy = (
        db.query(ChecklistPolicy)
        .filter(
            ChecklistPolicy.filiere == filiere,
            ChecklistPolicy.operation == operation,
            ChecklistPolicy.status == "active",
            ChecklistPolicy.effective_from <= lot_now(),
        )
        .order_by(ChecklistPolicy.id.desc())
        .first()
    )
    if not policy:
        return
    if category and policy.category and policy.category != category:
        return
    required_doc_types = json.loads(policy.required_doc_types_json or "[]")
    if not required_doc_types:
        return
    docs = (
        db.query(Document.doc_type)
        .filter(Document.id.in_(document_ids), Document.owner_actor_id == actor_id)
        .all()
    )
    present = {d[0] for d in docs}
    missing = [doc_type for doc_type in required_doc_types if doc_type not in present]
    if missing:
        raise bad_request("checklist_incomplete", {"missing_doc_types": missing})


def _infer_wood_classification(essence: EssenceCatalog, payload: LotCreate) -> str:
    attrs = payload.attributes or {}
    illegal_flag = bool(attrs.get("illegal_flag")) or bool(attrs.get("illegal"))
    if illegal_flag:
        return "ILLEGAL"
    if bool(essence.requires_cites) or not bool(essence.export_autorise):
        return "LEGAL_NON_EXPORTABLE"
    return "LEGAL_EXPORTABLE"


def _merge_wood_classification(lots: list[Lot]) -> str | None:
    if not lots:
        return None
    order = {
        "LEGAL_EXPORTABLE": 0,
        "LEGAL_NON_EXPORTABLE": 1,
        "ILLEGAL": 2,
        "A_DETRUIRE": 3,
    }
    values = [x.wood_classification for x in lots if x.wood_classification in order]
    if not values:
        return None
    return max(values, key=lambda x: order[x])


def _parse_destruction_evidence(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
        return loaded if isinstance(loaded, list) else []
    except Exception:
        return []


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
    if actor.status != "active":
        raise bad_request("compte_inactif")
    if payload.filiere == "OR" and payload.unit not in {"g", "kg", "akotry"}:
        raise bad_request("unite_non_autorisee")
    if payload.filiere == "OR":
        allowed, reason = can_declare_or_lot(db, actor.id)
        if not allowed:
            raise bad_request(reason or "or_declaration_bloquee")
    if payload.filiere == "PIERRE":
        if actor.status != "active":
            raise bad_request("compte_inactif")
        if not payload.sous_filiere:
            raise bad_request("sous_filiere_obligatoire")
        auth = (
            db.query(ActorAuthorization.id)
            .filter(
                ActorAuthorization.actor_id == actor.id,
                ActorAuthorization.filiere == "PIERRE",
                ActorAuthorization.status == "active",
                ActorAuthorization.valid_from <= lot_now(),
                ActorAuthorization.valid_to >= lot_now(),
            )
            .first()
        )
        if not auth:
            raise bad_request("autorisation_expiree")
        if not payload.product_catalog_id:
            raise bad_request("product_catalog_obligatoire")
        product = db.query(ProductCatalog).filter_by(id=payload.product_catalog_id, status="active").first()
        if not product:
            raise bad_request("catalog_produit_introuvable")
        if product.filiere != "PIERRE":
            raise bad_request("catalog_filiere_invalide")
        if product.sous_filiere != payload.sous_filiere:
            raise bad_request("catalog_sous_filiere_invalide")
        allowed_units = set(json.loads(product.allowed_units_json or "[]"))
        if allowed_units and payload.unit not in allowed_units:
            raise bad_request("unite_non_autorisee")
        required_attrs = set(json.loads(product.required_attributes_json or "[]"))
        incoming_attrs = payload.attributes or {}
        missing = sorted([key for key in required_attrs if key not in incoming_attrs or incoming_attrs.get(key) in (None, "", [])])
        if missing:
            raise bad_request("attributs_catalogue_manquants", {"missing": missing})
    wood_classification = None
    cites_laf_status = None
    cites_ndf_status = None
    cites_international_status = None

    if payload.filiere == "BOIS":
        allowed_roles = {
            "admin",
            "dirigeant",
            "forets",
            "bois_exploitant",
            "bois_collecteur",
            "bois_transformateur",
            "bois_artisan",
            "bois_exportateur",
            "bois_admin_central",
        }
        if _active_roles(db, actor.id).isdisjoint(allowed_roles):
            raise bad_request("role_insuffisant")
        _ensure_active_authorization(db, actor.id, "BOIS")
        if not payload.wood_essence_id:
            raise bad_request("wood_essence_obligatoire")
        if not payload.wood_form:
            raise bad_request("wood_form_obligatoire")
        essence = db.query(EssenceCatalog).filter_by(id=payload.wood_essence_id, status="active").first()
        if not essence:
            raise bad_request("essence_introuvable")
        if payload.wood_form not in {"tronc", "grume", "billon", "planche", "lot_scie", "produit_fini"}:
            raise bad_request("wood_form_invalide")
        if payload.unit not in {"m3", "piece", "kg"}:
            raise bad_request("unite_non_autorisee")
        if payload.unit == "m3" and payload.volume_m3 is None:
            raise bad_request("volume_m3_obligatoire")
        _check_required_docs(
            db=db,
            actor_id=actor.id,
            filiere="BOIS",
            operation="declaration",
            category=essence.categorie,
            document_ids=payload.document_ids or [],
        )
        wood_classification = _infer_wood_classification(essence, payload)
        requires_cites = bool(essence.requires_cites)
        cites_laf_status = "required" if requires_cites else "not_required"
        cites_ndf_status = "required" if requires_cites else "not_required"
        cites_international_status = "required" if requires_cites else "not_required"

    lot = Lot(
        filiere=payload.filiere,
        sous_filiere=payload.sous_filiere,
        product_catalog_id=payload.product_catalog_id,
        wood_essence_id=payload.wood_essence_id,
        wood_form=payload.wood_form,
        volume_m3=payload.volume_m3,
        attributes_json=json.dumps(payload.attributes or {}, ensure_ascii=True),
        product_type=payload.product_type,
        unit=payload.unit,
        quantity=payload.quantity,
        declared_by_actor_id=payload.declared_by_actor_id,
        current_owner_actor_id=payload.declared_by_actor_id,
        status="suspect" if wood_classification == "ILLEGAL" else "available",
        declare_geo_point_id=payload.declare_geo_point_id,
        notes=payload.notes,
        photo_urls_json=json.dumps(payload.photo_urls, ensure_ascii=True),
        wood_classification=wood_classification,
        cites_laf_status=cites_laf_status,
        cites_ndf_status=cites_ndf_status,
        cites_international_status=cites_international_status,
    )
    db.add(lot)
    db.flush()
    origin_ref = _resolve_origin_reference(db, actor_id=actor.id, filiere=payload.filiere)
    lot.origin_reference = origin_ref
    lot.lot_number = build_lot_number(
        region_code=_actor_region_code(db, actor.id),
        permit_ref=origin_ref.split(":", 1)[-1],
        lot_id=lot.id,
    )
    lot.traceability_id = build_traceability_id(
        lot_number=lot.lot_number,
        origin_ref=origin_ref,
        lot_id=lot.id,
    )
    lot.declaration_receipt_number = build_receipt_number("LOT", lot.id)
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
    db.flush()
    _refresh_lot_trace(
        db,
        lot,
        event_type="create",
        event_ref=str(lot.id),
        previous_hash=None,
    )
    lot.declaration_receipt_document_id = _create_lot_receipt_document(db, lot)
    write_audit(
        db,
        actor_id=payload.declared_by_actor_id,
        action="lot_created",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={"quantity": str(payload.quantity), "unit": payload.unit, "receipt": lot.declaration_receipt_number},
    )
    db.commit()
    db.refresh(lot)
    return _to_lot_out(lot)


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

    total = query.count()
    lots = (
        query.order_by(Lot.declared_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )
    items = [_to_lot_out(lot) for lot in lots]
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
    return _to_lot_out(lot)


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
    if lot.filiere == "OR":
        allowed, reason = can_trade_or(db, current_actor.id, payload.new_owner_actor_id)
        if not allowed:
            raise bad_request(reason or "transaction_or_bloquee")
        transport_ok = (
            db.query(TransportEvent.id)
            .filter(
                TransportEvent.lot_id == lot.id,
                TransportEvent.depart_actor_id == current_actor.id,
                TransportEvent.arrival_actor_id == payload.new_owner_actor_id,
                TransportEvent.status.in_(["in_transit", "delivered"]),
            )
            .first()
        )
        if not transport_ok:
            lot.status = "suspect"
            db.commit()
            raise bad_request("transport_non_declare")

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
    db.flush()
    _refresh_lot_trace(
        db,
        lot,
        event_type="transfer",
        event_ref=str(payment.id),
        previous_hash=lot.current_block_hash,
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
    return _to_lot_out(lot)


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
    merged_classification = _merge_wood_classification(lots)
    merged_laf = "required" if any((x.cites_laf_status or "") in {"required", "pending", "approved", "rejected"} for x in lots) else "not_required"
    merged_ndf = "required" if any((x.cites_ndf_status or "") in {"required", "pending", "approved", "rejected"} for x in lots) else "not_required"
    merged_international = "required" if any((x.cites_international_status or "") in {"required", "pending", "approved", "rejected"} for x in lots) else "not_required"
    parent = Lot(
        filiere=lots[0].filiere,
        sous_filiere=lots[0].sous_filiere,
        product_catalog_id=lots[0].product_catalog_id,
        wood_essence_id=lots[0].wood_essence_id,
        wood_form=lots[0].wood_form,
        volume_m3=lots[0].volume_m3,
        attributes_json=lots[0].attributes_json,
        product_type=payload.product_type,
        unit=payload.unit,
        quantity=total,
        declared_by_actor_id=current_actor.id,
        current_owner_actor_id=current_actor.id,
        status="suspect" if merged_classification == "ILLEGAL" else "available",
        declare_geo_point_id=payload.declare_geo_point_id,
        wood_classification=merged_classification,
        cites_laf_status=merged_laf,
        cites_ndf_status=merged_ndf,
        cites_international_status=merged_international,
    )
    db.add(parent)
    db.flush()
    parent.origin_reference = lots[0].origin_reference or _resolve_origin_reference(db, actor_id=current_actor.id, filiere=lots[0].filiere)
    parent.lot_number = build_lot_number(
        region_code=_actor_region_code(db, current_actor.id),
        permit_ref=(parent.origin_reference or "").split(":", 1)[-1],
        lot_id=parent.id,
    )
    parent.traceability_id = build_traceability_id(
        lot_number=parent.lot_number,
        origin_ref=parent.origin_reference or "PERMIS:INCONNU",
        lot_id=parent.id,
    )
    parent.declaration_receipt_number = build_receipt_number("LOT", parent.id)
    parent_prev_hash = compute_chain_hash(
        {
            "event": "consolidate_seed",
            "child_hashes": sorted([(lot.current_block_hash or "") for lot in lots]),
        }
    )
    child_traces: list[tuple[Lot, str | None]] = []
    for lot in lots:
        previous_hash = lot.current_block_hash
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
        child_traces.append((lot, previous_hash))
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
    db.flush()
    for lot, previous_hash in child_traces:
        _refresh_lot_trace(
            db,
            lot,
            event_type="consolidate_out",
            event_ref=str(parent.id),
            previous_hash=previous_hash,
        )
    _refresh_lot_trace(
        db,
        parent,
        event_type="consolidate_in",
        event_ref=str(parent.id),
        previous_hash=parent_prev_hash,
    )
    parent.declaration_receipt_document_id = _create_lot_receipt_document(db, parent)
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
    return _to_lot_out(parent)


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
    parent_previous_hash = lot.current_block_hash
    for qty in payload.quantities:
        child = Lot(
            filiere=lot.filiere,
            sous_filiere=lot.sous_filiere,
            product_catalog_id=lot.product_catalog_id,
            wood_essence_id=lot.wood_essence_id,
            wood_form=lot.wood_form,
            volume_m3=lot.volume_m3,
            attributes_json=lot.attributes_json,
            product_type=lot.product_type,
            unit=lot.unit,
            quantity=qty,
            declared_by_actor_id=current_actor.id,
            current_owner_actor_id=current_actor.id,
            status="suspect" if lot.wood_classification == "ILLEGAL" else "available",
            declare_geo_point_id=lot.declare_geo_point_id,
            parent_lot_id=lot.id,
            notes=lot.notes,
            photo_urls_json=lot.photo_urls_json,
            wood_classification=lot.wood_classification,
            cites_laf_status=lot.cites_laf_status,
            cites_ndf_status=lot.cites_ndf_status,
            cites_international_status=lot.cites_international_status,
            destruction_status=lot.destruction_status,
            destruction_requested_at=lot.destruction_requested_at,
            destruction_validated_at=lot.destruction_validated_at,
            destruction_evidence_json=lot.destruction_evidence_json,
        )
        db.add(child)
        db.flush()
        child.origin_reference = lot.origin_reference or _resolve_origin_reference(db, actor_id=current_actor.id, filiere=lot.filiere)
        child.lot_number = build_lot_number(
            region_code=_actor_region_code(db, current_actor.id),
            permit_ref=(child.origin_reference or "").split(":", 1)[-1],
            lot_id=child.id,
        )
        child.traceability_id = build_traceability_id(
            lot_number=child.lot_number,
            origin_ref=child.origin_reference or "PERMIS:INCONNU",
            lot_id=child.id,
        )
        child.declaration_receipt_number = build_receipt_number("LOT", child.id)
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
    db.flush()
    _refresh_lot_trace(
        db,
        lot,
        event_type="split_out",
        event_ref=str(lot.id),
        previous_hash=parent_previous_hash,
    )
    for child in children:
        _refresh_lot_trace(
            db,
            child,
            event_type="split_in",
            event_ref=str(lot.id),
            previous_hash=parent_previous_hash,
        )
        child.declaration_receipt_document_id = _create_lot_receipt_document(db, child)
    write_audit(
        db,
        actor_id=current_actor.id,
        action="lot_split",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={"child_lot_ids": [c.id for c in children]},
    )
    db.commit()
    return [_to_lot_out(child) for child in children]


@router.patch("/{lot_id}/wood-classification", response_model=LotOut)
def patch_wood_classification(
    lot_id: int,
    payload: LotWoodClassificationPatch,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    if lot.filiere != "BOIS":
        raise bad_request("lot_non_bois")
    roles = _active_roles(db, current_actor.id)
    allowed = {"admin", "dirigeant", "forets", "bois_admin_central", "bois_controleur", "bois_douanes"}
    if roles.isdisjoint(allowed):
        raise bad_request("acces_refuse")

    now = lot_now()
    if payload.wood_classification is not None:
        value = payload.wood_classification.strip().upper()
        if value not in WOOD_CLASSIFICATIONS:
            raise bad_request("classification_bois_invalide", {"allowed": sorted(WOOD_CLASSIFICATIONS)})
        lot.wood_classification = value
        if value in {"ILLEGAL", "A_DETRUIRE"}:
            lot.status = "suspect"
        elif lot.status == "suspect":
            lot.status = "available"

    if payload.cites_laf_status is not None:
        value = payload.cites_laf_status.strip().lower()
        if value not in CITES_STATUSES:
            raise bad_request("laf_status_invalide", {"allowed": sorted(CITES_STATUSES)})
        lot.cites_laf_status = value
    if payload.cites_ndf_status is not None:
        value = payload.cites_ndf_status.strip().lower()
        if value not in CITES_STATUSES:
            raise bad_request("ndf_status_invalide", {"allowed": sorted(CITES_STATUSES)})
        lot.cites_ndf_status = value
    if payload.cites_international_status is not None:
        value = payload.cites_international_status.strip().lower()
        if value not in CITES_STATUSES:
            raise bad_request("cites_status_invalide", {"allowed": sorted(CITES_STATUSES)})
        lot.cites_international_status = value

    if payload.destruction_status is not None:
        status = payload.destruction_status.strip().lower()
        if status not in DESTRUCTION_STATUSES:
            raise bad_request("destruction_status_invalide", {"allowed": sorted(DESTRUCTION_STATUSES)})
        lot.destruction_status = status
        if status in {"pending", "approved"} and lot.destruction_requested_at is None:
            lot.destruction_requested_at = now
        if status in {"validated", "destroyed"}:
            evidence = payload.destruction_evidence_urls or _parse_destruction_evidence(lot.destruction_evidence_json)
            if not evidence:
                raise bad_request("preuve_destruction_obligatoire")
            lot.destruction_validated_at = now

    if payload.destruction_evidence_urls is not None:
        lot.destruction_evidence_json = json.dumps(payload.destruction_evidence_urls, ensure_ascii=True)

    if lot.wood_classification == "A_DETRUIRE" and not lot.destruction_status:
        lot.destruction_status = "pending"
        lot.destruction_requested_at = now

    if payload.notes:
        lot.notes = payload.notes

    db.flush()
    _refresh_lot_trace(
        db,
        lot,
        event_type="wood_classification",
        event_ref=f"{current_actor.id}",
        previous_hash=lot.current_block_hash,
    )
    write_audit(
        db,
        actor_id=current_actor.id,
        action="lot_wood_classification_patched",
        entity_type="lot",
        entity_id=str(lot.id),
        meta={
            "classification": lot.wood_classification,
            "laf": lot.cites_laf_status,
            "ndf": lot.cites_ndf_status,
            "international": lot.cites_international_status,
            "destruction": lot.destruction_status,
        },
    )
    db.commit()
    db.refresh(lot)
    return _to_lot_out(lot)


def _parse_photo_urls(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
        return loaded if isinstance(loaded, list) else []
    except Exception:
        return []


def _actor_region_code(db: Session, actor_id: int) -> str | None:
    actor = db.query(Actor).filter(Actor.id == actor_id).first()
    if not actor or not actor.region_id:
        return None
    region = db.query(Region).filter(Region.id == actor.region_id).first()
    return region.code if region else None


def _resolve_origin_reference(db: Session, actor_id: int, filiere: str) -> str:
    target_filiere = (filiere or "").strip().upper()
    if target_filiere == "OR":
        kara = (
            db.query(KaraBolamenaCard)
            .filter(KaraBolamenaCard.actor_id == actor_id)
            .filter(KaraBolamenaCard.status.in_(["active", "validated"]))
            .order_by(KaraBolamenaCard.id.desc())
            .first()
        )
        if kara and kara.card_number:
            return f"KARABOLA:{kara.card_number}"
        collector = (
            db.query(CollectorCard)
            .filter(CollectorCard.actor_id == actor_id)
            .filter(CollectorCard.status.in_(["active", "validated"]))
            .order_by(CollectorCard.id.desc())
            .first()
        )
        if collector and collector.card_number:
            return f"KARABOLA:{collector.card_number}"

    auth = (
        db.query(ActorAuthorization)
        .filter(
            ActorAuthorization.actor_id == actor_id,
            ActorAuthorization.filiere == target_filiere,
            ActorAuthorization.status == "active",
        )
        .order_by(ActorAuthorization.valid_to.desc(), ActorAuthorization.id.desc())
        .first()
    )
    if auth and auth.numero:
        return f"PERMIS:{auth.numero}"
    return f"PERMIS:ACTOR-{actor_id}"


def _lot_history_refs(db: Session, lot_id: int, limit: int = 6) -> list[str]:
    rows = (
        db.query(InventoryLedger)
        .filter(InventoryLedger.lot_id == lot_id)
        .order_by(InventoryLedger.created_at.asc(), InventoryLedger.id.asc())
        .all()
    )
    refs = [
        f"{row.movement_type}:{row.ref_event_type}:{row.ref_event_id}"
        for row in rows
    ]
    if len(refs) <= limit:
        return refs
    return refs[-limit:]


def _refresh_lot_trace(
    db: Session,
    lot: Lot,
    *,
    event_type: str,
    event_ref: str,
    previous_hash: str | None,
) -> None:
    prior_hash = previous_hash or lot.current_block_hash or "GENESIS"
    history = _lot_history_refs(db, lot.id, limit=8)
    payload = {
        "lot_id": lot.id,
        "lot_number": lot.lot_number,
        "traceability_id": lot.traceability_id,
        "origin_reference": lot.origin_reference,
        "event_type": event_type,
        "event_ref": event_ref,
        "history": history,
        "previous_block_hash": prior_hash,
    }
    current_hash = compute_chain_hash(payload)
    lot.previous_block_hash = prior_hash
    lot.current_block_hash = current_hash
    lot.trace_payload_json = canonical_json(payload)

    qr_history = history[-4:]
    qr_payload = {
        "lot_id": lot.id,
        "origin": lot.origin_reference,
        "history": qr_history,
        "prev_hash": prior_hash,
        "hash": current_hash,
    }
    qr_value = json.dumps(qr_payload, separators=(",", ":"), ensure_ascii=True)
    while len(qr_value) > 255 and len(qr_history) > 1:
        qr_history = qr_history[1:]
        qr_payload["history"] = qr_history
        qr_value = json.dumps(qr_payload, separators=(",", ":"), ensure_ascii=True)
    if len(qr_value) > 255:
        qr_payload = {
            "lot_id": lot.id,
            "origin": lot.origin_reference,
            "event": f"{event_type}:{event_ref}",
            "prev_hash": prior_hash,
            "hash": current_hash,
        }
        qr_value = json.dumps(qr_payload, separators=(",", ":"), ensure_ascii=True)
    lot.qr_code = qr_value[:255]


def _create_lot_receipt_document(db: Session, lot: Lot) -> int:
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{lot.declaration_receipt_number}.pdf"
    content = build_simple_pdf(
        title="Recu de declaration de lot",
        lines=[
            f"Numero: {lot.declaration_receipt_number}",
            f"Numero lot: {lot.lot_number or '-'}",
            f"ID tracabilite: {lot.traceability_id or '-'}",
            f"Origine: {lot.origin_reference or '-'}",
            f"Lot ID: {lot.id}",
            f"Filiere: {lot.filiere}",
            f"Produit: {lot.product_type}",
            f"Quantite: {lot.quantity} {lot.unit}",
            f"Declare par acteur: {lot.declared_by_actor_id}",
            f"QR: {lot.qr_code}",
        ],
    )
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    doc = Document(
        doc_type="lot_receipt",
        owner_actor_id=lot.declared_by_actor_id,
        related_entity_type="lot",
        related_entity_id=str(lot.id),
        storage_path=str(storage_path),
        original_filename=filename,
        sha256=sha256,
    )
    db.add(doc)
    db.flush()
    return doc.id


def _to_lot_out(lot: Lot) -> LotOut:
    attrs = {}
    if lot.attributes_json:
        try:
            attrs = json.loads(lot.attributes_json)
        except Exception:
            attrs = {}
    return LotOut(
        id=lot.id,
        filiere=lot.filiere,
        sous_filiere=lot.sous_filiere,
        product_catalog_id=lot.product_catalog_id,
        wood_essence_id=lot.wood_essence_id,
        wood_form=lot.wood_form,
        volume_m3=float(lot.volume_m3) if lot.volume_m3 is not None else None,
        attributes=attrs,
        product_type=lot.product_type,
        unit=lot.unit,
        quantity=float(lot.quantity),
        declared_at=lot.declared_at,
        declared_by_actor_id=lot.declared_by_actor_id,
        current_owner_actor_id=lot.current_owner_actor_id,
        status=lot.status,
        declare_geo_point_id=lot.declare_geo_point_id,
        notes=lot.notes,
        photo_urls=_parse_photo_urls(lot.photo_urls_json),
        qr_code=lot.qr_code,
        declaration_receipt_number=lot.declaration_receipt_number,
        declaration_receipt_document_id=lot.declaration_receipt_document_id,
        lot_number=lot.lot_number,
        traceability_id=lot.traceability_id,
        origin_reference=lot.origin_reference,
        previous_block_hash=lot.previous_block_hash,
        current_block_hash=lot.current_block_hash,
        wood_classification=lot.wood_classification,
        cites_laf_status=lot.cites_laf_status,
        cites_ndf_status=lot.cites_ndf_status,
        cites_international_status=lot.cites_international_status,
        destruction_status=lot.destruction_status,
        destruction_requested_at=lot.destruction_requested_at,
        destruction_validated_at=lot.destruction_validated_at,
        destruction_evidence_urls=_parse_destruction_evidence(lot.destruction_evidence_json),
    )


def lot_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
