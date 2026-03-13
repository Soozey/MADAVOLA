import hashlib
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.common.card_identity import build_invoice_number, build_receipt_number, canonical_json, sha256_hex, sign_hmac_sha256
from app.common.receipts import build_qr_value, build_simple_pdf
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.document import Document
from app.models.invoice import Invoice
from app.models.lot import InventoryLedger, Lot
from app.models.payment import Payment, PaymentProvider, PaymentRequest
from app.models.pierre import ActorAuthorization
from app.models.tax import TaxRecord
from app.models.territory import Region
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.trades.schemas import TradeCreate, TradeItemCreate, TradeOut, TradePayIn

router = APIRouter(prefix=f"{settings.api_prefix}/trades", tags=["trades"])


def _roles(db: Session, actor_id: int) -> set[str]:
    rows = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    return {r[0] for r in rows}


def _ensure_pierre_trade_path(db: Session, seller_id: int, buyer_id: int) -> None:
    seller_roles = _roles(db, seller_id)
    buyer_roles = _roles(db, buyer_id)
    allowed = False
    if "pierre_exploitant" in seller_roles and "pierre_collecteur" in buyer_roles:
        allowed = True
    if "pierre_collecteur" in seller_roles and buyer_roles.intersection({"pierre_collecteur", "pierre_lapidaire", "pierre_exportateur"}):
        allowed = True
    if "pierre_lapidaire" in seller_roles and buyer_roles.intersection({"pierre_exportateur", "pierre_collecteur"}):
        allowed = True
    if {"admin", "dirigeant"}.intersection(seller_roles):
        allowed = True
    if not allowed:
        raise bad_request("rbac_trade_pierre_refuse")


def _ensure_bois_trade_path(db: Session, seller_id: int, buyer_id: int) -> None:
    seller_roles = _roles(db, seller_id)
    buyer_roles = _roles(db, buyer_id)
    allowed = False
    if "bois_exploitant" in seller_roles and buyer_roles.intersection({"bois_collecteur", "bois_transformateur"}):
        allowed = True
    if "bois_collecteur" in seller_roles and buyer_roles.intersection({"bois_collecteur", "bois_transformateur", "bois_exportateur"}):
        allowed = True
    if "bois_transformateur" in seller_roles and buyer_roles.intersection({"bois_artisan", "bois_exportateur"}):
        allowed = True
    if "bois_artisan" in seller_roles and "bois_exportateur" in buyer_roles:
        allowed = True
    if {"admin", "dirigeant", "forets", "bois_admin_central"}.intersection(seller_roles):
        allowed = True
    if not allowed:
        raise bad_request("rbac_trade_bois_refuse")


def _ensure_active_authorization(db: Session, actor_id: int, filiere: str) -> None:
    now = datetime.now(timezone.utc)
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


def _sum_items(items: list[TradeItemCreate]) -> Decimal:
    total = Decimal("0")
    for i in items:
        total += Decimal(str(i.quantity)) * Decimal(str(i.unit_price))
    return total


def _issue_trade_invoice_and_receipt(db: Session, tx: TradeTransaction) -> None:
    now = datetime.now(timezone.utc)
    invoice = db.query(Invoice).filter(Invoice.transaction_id == tx.id).first()
    items = db.query(TradeTransactionItem).filter(TradeTransactionItem.transaction_id == tx.id).all()
    lots = (
        db.query(Lot).filter(Lot.id.in_([item.lot_id for item in items if item.lot_id is not None])).all()
        if items
        else []
    )
    filiere = (lots[0].filiere if lots else "OR") or "OR"
    origin_reference = None
    lot_refs = []
    unit = None
    qty_total = 0.0
    if lots:
        origin_candidates = [x.origin_reference for x in lots if x.origin_reference]
        origin_reference = origin_candidates[0] if origin_candidates else None
        if len(set(origin_candidates)) > 1:
            origin_reference = "MIXED_ORIGIN"
    for item in items:
        qty_total += float(item.quantity)
        lot = next((x for x in lots if x.id == item.lot_id), None)
        if lot:
            lot_refs.append(lot.lot_number or f"LOT-{lot.id}")
    units = [x.unit for x in lots if x.unit]
    if len(set(units)) == 1 and units:
        unit = units[0]
    elif units:
        unit = "mixed"

    seller = db.query(Actor).filter_by(id=tx.seller_actor_id).first()
    region_code = None
    if seller and seller.region_id:
        region = db.query(Region).filter_by(id=seller.region_id).first()
        region_code = region.code if region else None

    taxes = db.query(TaxRecord).filter(TaxRecord.transaction_id == tx.id).order_by(TaxRecord.id.asc()).all()
    taxes_json = [
        {
            "id": row.id,
            "tax_type": row.tax_type,
            "beneficiary_level": row.beneficiary_level,
            "beneficiary_key": row.beneficiary_key,
            "rate": float(row.tax_rate),
            "amount": float(row.tax_amount),
            "status": row.status,
        }
        for row in taxes
    ]
    subtotal_ht = float(tx.total_amount)
    taxes_total = round(sum(x["amount"] for x in taxes_json), 2)
    total_ttc = round(subtotal_ht + taxes_total, 2)
    unit_price_avg = round(subtotal_ht / qty_total, 2) if qty_total > 0 else None
    previous = db.query(Invoice).filter(Invoice.transaction_id != tx.id).order_by(Invoice.issue_date.desc(), Invoice.id.desc()).first()
    previous_hash = previous.invoice_hash if previous and previous.invoice_hash else "GENESIS"
    payload = {
        "transaction_id": tx.id,
        "seller_actor_id": tx.seller_actor_id,
        "buyer_actor_id": tx.buyer_actor_id,
        "filiere": filiere,
        "region_code": region_code,
        "origin_reference": origin_reference,
        "lot_refs": lot_refs,
        "subtotal_ht": subtotal_ht,
        "taxes": taxes_json,
        "total_ttc": total_ttc,
        "previous_invoice_hash": previous_hash,
        "issued_at": now.isoformat(),
    }
    invoice_hash = sha256_hex(canonical_json(payload))
    signature = sign_hmac_sha256(settings.card_qr_signing_secret or settings.jwt_secret, invoice_hash)

    if not invoice:
        invoice_number = build_invoice_number(tx.id, filiere=filiere, region_code=region_code, now=now)
        invoice = Invoice(
            invoice_number=invoice_number,
            transaction_id=tx.id,
            seller_actor_id=tx.seller_actor_id,
            buyer_actor_id=tx.buyer_actor_id,
            total_amount=tx.total_amount,
            status="paid",
            qr_code=build_qr_value("invoice", invoice_number),
            filiere=filiere,
            region_code=region_code,
            origin_reference=origin_reference,
            lot_references_json=json.dumps(lot_refs, ensure_ascii=True),
            quantity_total=qty_total,
            unit=unit,
            unit_price_avg=unit_price_avg,
            subtotal_ht=subtotal_ht,
            taxes_json=json.dumps(taxes_json, ensure_ascii=True),
            taxes_total=taxes_total,
            total_ttc=total_ttc,
            previous_invoice_hash=previous_hash,
            invoice_hash=invoice_hash,
            internal_signature=signature,
            trace_payload_json=canonical_json(payload),
            is_immutable=True,
        )
        db.add(invoice)
        db.flush()
        invoice_pdf = build_simple_pdf(
            "MADAVOLA - Facture transaction",
            [
                f"Facture: {invoice_number}",
                f"Transaction: {tx.id}",
                f"Vendeur: {tx.seller_actor_id}",
                f"Acheteur: {tx.buyer_actor_id}",
                f"Origine: {origin_reference or '-'}",
                f"Lots: {', '.join(lot_refs) if lot_refs else '-'}",
                f"Total HT: {subtotal_ht:.2f} {tx.currency}",
                f"Taxes: {taxes_total:.2f} {tx.currency}",
                f"Total TTC: {total_ttc:.2f} {tx.currency}",
                f"Hash facture: {invoice_hash}",
                f"Date: {now.isoformat()}",
            ],
        )
        invoice_filename = f"{invoice_number}.pdf"
        invoice_path = Path(settings.document_storage_dir) / invoice_filename
        invoice_path.parent.mkdir(parents=True, exist_ok=True)
        invoice_path.write_bytes(invoice_pdf)
        db.add(
            Document(
                doc_type="invoice",
                owner_actor_id=tx.seller_actor_id,
                related_entity_type="invoice",
                related_entity_id=str(invoice.id),
                storage_path=str(invoice_path),
                original_filename=invoice_filename,
                sha256=hashlib.sha256(invoice_pdf).hexdigest(),
            )
        )
    invoice.status = "paid"
    if not invoice.receipt_document_id:
        receipt_number = build_receipt_number(invoice.id, now=now)
        receipt_pdf = build_simple_pdf(
            "MADAVOLA - Recu transaction",
            [
                f"Recu: {receipt_number}",
                f"Facture: {invoice.invoice_number}",
                f"Transaction: {tx.id}",
                "Paiement: cash_declared",
                f"Payeur: {tx.buyer_actor_id}",
                f"Beneficiaire: {tx.seller_actor_id}",
                f"Montant TTC: {total_ttc:.2f} {tx.currency}",
                f"Hash facture: {invoice.invoice_hash or invoice_hash}",
                f"Date confirmation: {now.isoformat()}",
            ],
        )
        receipt_filename = f"{receipt_number}.pdf"
        receipt_path = Path(settings.document_storage_dir) / receipt_filename
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_bytes(receipt_pdf)
        doc = Document(
            doc_type="receipt",
            owner_actor_id=tx.buyer_actor_id,
            related_entity_type="invoice",
            related_entity_id=str(invoice.id),
            storage_path=str(receipt_path),
            original_filename=receipt_filename,
            sha256=hashlib.sha256(receipt_pdf).hexdigest(),
        )
        db.add(doc)
        db.flush()
        invoice.receipt_number = receipt_number
        invoice.receipt_document_id = doc.id


@router.post("", response_model=TradeOut, status_code=201)
def create_trade(
    payload: TradeCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if current_actor.id != payload.seller_actor_id:
        raise bad_request("acces_refuse")
    if not payload.items:
        raise bad_request("items_obligatoires")
    seller = db.query(Actor).filter_by(id=payload.seller_actor_id).first()
    buyer = db.query(Actor).filter_by(id=payload.buyer_actor_id).first()
    if not seller or not buyer:
        raise bad_request("acteur_invalide")

    for item in payload.items:
        lot = db.query(Lot).filter_by(id=item.lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable")
        if lot.current_owner_actor_id != payload.seller_actor_id:
            raise bad_request("lot_non_proprietaire")
        if lot.status == "exported":
            raise bad_request("lot_exported_transfer_blocked")
        if lot.filiere == "PIERRE":
            _ensure_active_authorization(db, payload.seller_actor_id, "PIERRE")
            _ensure_active_authorization(db, payload.buyer_actor_id, "PIERRE")
            _ensure_pierre_trade_path(db, payload.seller_actor_id, payload.buyer_actor_id)
        if lot.filiere == "BOIS":
            _ensure_active_authorization(db, payload.seller_actor_id, "BOIS")
            _ensure_active_authorization(db, payload.buyer_actor_id, "BOIS")
            _ensure_bois_trade_path(db, payload.seller_actor_id, payload.buyer_actor_id)

    tx = TradeTransaction(
        seller_actor_id=payload.seller_actor_id,
        buyer_actor_id=payload.buyer_actor_id,
        status="draft",
        total_amount=_sum_items(payload.items),
        currency=payload.currency,
    )
    db.add(tx)
    db.flush()
    for item in payload.items:
        db.add(
            TradeTransactionItem(
                transaction_id=tx.id,
                lot_id=item.lot_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_amount=Decimal(str(item.quantity)) * Decimal(str(item.unit_price)),
            )
        )
    db.commit()
    db.refresh(tx)
    return TradeOut(
        id=tx.id,
        seller_actor_id=tx.seller_actor_id,
        buyer_actor_id=tx.buyer_actor_id,
        status=tx.status,
        total_amount=float(tx.total_amount),
        currency=tx.currency,
    )


@router.post("/{trade_id}/pay", response_model=TradeOut)
def pay_trade(
    trade_id: int,
    payload: TradePayIn,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    tx = db.query(TradeTransaction).filter_by(id=trade_id).first()
    if not tx:
        raise bad_request("transaction_introuvable")
    if current_actor.id not in {tx.buyer_actor_id, tx.seller_actor_id}:
        raise bad_request("acces_refuse")
    if tx.status not in {"draft", "pending_payment"}:
        raise bad_request("transaction_invalide")

    mode = (payload.payment_mode or "").strip().lower()
    if mode == "cash_declared":
        tx.status = "paid"
        db.commit()
    else:
        provider_code = payload.provider_code or "mvola"
        provider = db.query(PaymentProvider).filter_by(code=provider_code).first()
        if not provider or not provider.enabled:
            raise bad_request("provider_indisponible")
        tx.status = "pending_payment"
        req = PaymentRequest(
            provider_id=provider.id,
            payer_actor_id=tx.buyer_actor_id,
            payee_actor_id=tx.seller_actor_id,
            transaction_id=tx.id,
            amount=tx.total_amount,
            currency=tx.currency,
            status="pending",
            external_ref=payload.external_ref or f"trade-{tx.id}",
            idempotency_key=payload.idempotency_key,
        )
        db.add(req)
        db.flush()
        db.add(Payment(payment_request_id=req.id, status="pending"))
        db.commit()
    db.refresh(tx)
    return TradeOut(
        id=tx.id,
        seller_actor_id=tx.seller_actor_id,
        buyer_actor_id=tx.buyer_actor_id,
        status=tx.status,
        total_amount=float(tx.total_amount),
        currency=tx.currency,
    )


@router.post("/{trade_id}/confirm", response_model=TradeOut)
def confirm_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    tx = db.query(TradeTransaction).filter_by(id=trade_id).first()
    if not tx:
        raise bad_request("transaction_introuvable")
    if current_actor.id not in {tx.buyer_actor_id, tx.seller_actor_id}:
        raise bad_request("acces_refuse")
    if tx.status != "paid":
        raise bad_request("transaction_non_payee")

    items = db.query(TradeTransactionItem).filter(TradeTransactionItem.transaction_id == tx.id).all()
    for item in items:
        lot = db.query(Lot).filter_by(id=item.lot_id).first()
        if not lot:
            raise bad_request("lot_introuvable")
        if lot.status == "exported":
            raise bad_request("lot_exported_transfer_blocked")
        qty = Decimal(str(item.quantity))
        if qty > Decimal(str(lot.quantity)):
            raise bad_request("quantite_superieure_stock")
        if qty == Decimal(str(lot.quantity)):
            lot.current_owner_actor_id = tx.buyer_actor_id
            lot.status = "available"
            db.add(
                InventoryLedger(
                    actor_id=tx.seller_actor_id,
                    lot_id=lot.id,
                    movement_type="transfer_out",
                    quantity_delta=-float(qty),
                    ref_event_type="trade_confirm",
                    ref_event_id=str(tx.id),
                )
            )
            db.add(
                InventoryLedger(
                    actor_id=tx.buyer_actor_id,
                    lot_id=lot.id,
                    movement_type="transfer_in",
                    quantity_delta=float(qty),
                    ref_event_type="trade_confirm",
                    ref_event_id=str(tx.id),
                )
            )
        else:
            lot.quantity = float(Decimal(str(lot.quantity)) - qty)
            child = Lot(
                filiere=lot.filiere,
                sous_filiere=lot.sous_filiere,
                product_catalog_id=lot.product_catalog_id,
                attributes_json=lot.attributes_json,
                product_type=lot.product_type,
                unit=lot.unit,
                quantity=float(qty),
                declared_by_actor_id=lot.declared_by_actor_id,
                current_owner_actor_id=tx.buyer_actor_id,
                status="available",
                declare_geo_point_id=lot.declare_geo_point_id,
                parent_lot_id=lot.id,
                notes=lot.notes,
                photo_urls_json=lot.photo_urls_json,
                qr_code=build_qr_value("lot", f"trade-{tx.id}-split-{lot.id}"),
            )
            db.add(child)
            db.flush()
            db.add(
                InventoryLedger(
                    actor_id=tx.seller_actor_id,
                    lot_id=lot.id,
                    movement_type="transfer_out",
                    quantity_delta=-float(qty),
                    ref_event_type="trade_confirm",
                    ref_event_id=str(tx.id),
                )
            )
            db.add(
                InventoryLedger(
                    actor_id=tx.buyer_actor_id,
                    lot_id=child.id,
                    movement_type="transfer_in",
                    quantity_delta=float(qty),
                    ref_event_type="trade_confirm",
                    ref_event_id=str(tx.id),
                )
            )
    tx.status = "transferred"
    _issue_trade_invoice_and_receipt(db, tx)
    db.commit()
    db.refresh(tx)
    return TradeOut(
        id=tx.id,
        seller_actor_id=tx.seller_actor_id,
        buyer_actor_id=tx.buyer_actor_id,
        status=tx.status,
        total_amount=float(tx.total_amount),
        currency=tx.currency,
    )
