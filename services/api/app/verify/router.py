"""
Endpoints publics de verification pour scan QR.
"""

from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.card_identity import verify_hmac_sha256
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.invoice import Invoice
from app.models.lot import InventoryLedger, Lot
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.territory import Commune
from app.verify.schemas import ActorVerifyOut, InvoiceVerifyOut, LotVerifyOut

router = APIRouter(prefix=f"{settings.api_prefix}/verify", tags=["verify"])


@router.get("/actor/{actor_id}", response_model=ActorVerifyOut)
def verify_actor(actor_id: int, db: Session = Depends(get_db)):
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    commune = db.query(Commune).filter_by(id=actor.commune_id).first() if actor.commune_id else None
    return ActorVerifyOut(
        id=actor.id,
        nom=actor.nom,
        prenoms=actor.prenoms,
        statut=actor.status,
        commune_code=commune.code if commune else "",
        type_personne=actor.type_personne,
    )


@router.get("/lot/{lot_id}", response_model=LotVerifyOut)
def verify_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter_by(id=lot_id).first()
    if not lot:
        raise bad_request("lot_introuvable")
    history_rows = (
        db.query(InventoryLedger)
        .filter(InventoryLedger.lot_id == lot.id)
        .order_by(InventoryLedger.created_at.desc(), InventoryLedger.id.desc())
        .limit(6)
        .all()
    )
    history = [
        f"{row.movement_type}:{row.ref_event_type}:{row.ref_event_id}"
        for row in history_rows
    ]
    return LotVerifyOut(
        id=lot.id,
        status=lot.status,
        current_owner_actor_id=lot.current_owner_actor_id,
        declared_by_actor_id=lot.declared_by_actor_id,
        filiere=lot.filiere,
        product_type=lot.product_type,
        quantity=float(lot.quantity),
        unit=lot.unit,
        declaration_receipt_number=lot.declaration_receipt_number,
        qr_code=lot.qr_code,
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
        transaction_history=history,
    )


@router.get("/invoice/{invoice_ref}", response_model=InvoiceVerifyOut)
def verify_invoice(invoice_ref: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_ref).first()
    if not invoice and invoice_ref.isdigit():
        invoice = db.query(Invoice).filter(Invoice.id == int(invoice_ref)).first()
    if not invoice:
        raise bad_request("facture_introuvable")
    lot_references: list[str] = []
    if invoice.lot_references_json:
        try:
            loaded = json.loads(invoice.lot_references_json)
            if isinstance(loaded, list):
                lot_references = [str(x) for x in loaded]
        except Exception:
            lot_references = []
    return InvoiceVerifyOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        transaction_id=invoice.transaction_id,
        seller_actor_id=invoice.seller_actor_id,
        buyer_actor_id=invoice.buyer_actor_id,
        filiere=invoice.filiere,
        region_code=invoice.region_code,
        origin_reference=invoice.origin_reference,
        lot_references=lot_references,
        subtotal_ht=float(invoice.subtotal_ht) if invoice.subtotal_ht is not None else None,
        taxes_total=float(invoice.taxes_total) if invoice.taxes_total is not None else None,
        total_ttc=float(invoice.total_ttc) if invoice.total_ttc is not None else None,
        total_amount=float(invoice.total_amount),
        status=invoice.status,
        qr_code=invoice.qr_code,
        invoice_hash=invoice.invoice_hash,
        previous_invoice_hash=invoice.previous_invoice_hash,
        internal_signature=invoice.internal_signature,
        receipt_number=invoice.receipt_number,
    )


@router.get("/card/{card_ref}")
def verify_card(card_ref: str, db: Session = Depends(get_db)):
    card_type = "kara_bolamena"
    card = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.card_number == card_ref).first()
    if not card and card_ref.isdigit():
        card = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.id == int(card_ref)).first()
    if not card:
        card_type = "collector_card"
        card = db.query(CollectorCard).filter(CollectorCard.card_number == card_ref).first()
    if not card and card_ref.isdigit():
        card = db.query(CollectorCard).filter(CollectorCard.id == int(card_ref)).first()
        card_type = "collector_card"
    if not card:
        raise bad_request("carte_introuvable")

    actor = db.query(Actor).filter(Actor.id == card.actor_id).first()
    commune_id = card.commune_id if card_type == "kara_bolamena" else card.issuing_commune_id
    commune = db.query(Commune).filter(Commune.id == commune_id).first()
    signing_secret = settings.card_qr_signing_secret or settings.jwt_secret

    status_map = {"active": "validated", "withdrawn": "revoked", "pending": "pending_payment"}
    status = status_map.get((card.status or "").lower(), (card.status or "pending_payment").lower())
    expires_at = card.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= datetime.now(timezone.utc):
        status = "expired"

    signature_valid = False
    if card.qr_payload_hash and card.qr_signature:
        signature_valid = verify_hmac_sha256(signing_secret, card.qr_payload_hash, card.qr_signature)

    status_label_map = {
        "validated": "valide",
        "expired": "expiree",
        "revoked": "retiree",
        "pending_payment": "en_attente",
    }
    status_label = status_label_map.get(status, status)

    return {
        "card_id": card.id,
        "card_type": card_type,
        "card_number": card.card_number,
        "card_uid": card.card_uid,
        "actor_id": card.actor_id,
        "full_name": f"{actor.nom} {actor.prenoms or ''}".strip() if actor else None,
        "commune_code": commune.code if commune else None,
        "status": status,
        "status_label": status_label,
        "validated_at": card.validated_at,
        "expires_at": card.expires_at,
        "qr_hash": card.qr_payload_hash,
        "signature_valid": signature_valid,
    }
