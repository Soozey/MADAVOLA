from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.common.card_identity import (
    build_invoice_number,
    build_receipt_number,
    canonical_json,
    sha256_hex,
    sign_hmac_sha256,
)
from app.core.config import settings
from app.db import get_db
from app.audit.logger import write_audit
from app.auth.dependencies import get_current_actor
from app.models.actor import Actor, ActorRole
from app.models.admin import SystemConfig
from app.models.fee import Fee
from app.models.invoice import Invoice
from app.models.document import Document
from app.models.lot import InventoryLedger, Lot
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.payment import Payment, PaymentProvider, PaymentRequest, WebhookInbox
from app.models.tax import TaxRecord
from app.models.territory import Region
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.or_compliance.fee_split import allocate_collector_card_fee_split
from app.payments.schemas import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentRequestOut,
    WebhookPayload,
)
from app.common.receipts import build_qr_value, build_simple_pdf

router = APIRouter(prefix=f"{settings.api_prefix}/payments", tags=["payments"])

@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=201)
def initiate_payment(
    payload: PaymentInitiate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    provider = db.query(PaymentProvider).filter_by(code=payload.provider_code).first()
    if not provider or not provider.enabled:
        raise bad_request("provider_indisponible")

    payer = db.query(Actor).filter_by(id=payload.payer_actor_id).first()
    payee = db.query(Actor).filter_by(id=payload.payee_actor_id).first()
    if not payer or not payee:
        raise bad_request("acteur_invalide")
    if not _is_admin(db, current_actor.id) and payload.payer_actor_id != current_actor.id:
        raise bad_request("acces_refuse")

    fee = None
    if payload.fee_id:
        fee = db.query(Fee).filter_by(id=payload.fee_id).first()
        if not fee or fee.status != "pending":
            raise bad_request("frais_invalide")
        if fee.actor_id != payload.payer_actor_id:
            raise bad_request("frais_invalide")

    transaction = None
    if payload.transaction_id:
        transaction = (
            db.query(TradeTransaction).filter_by(id=payload.transaction_id).first()
        )
        if not transaction or transaction.status != "pending_payment":
            raise bad_request("transaction_invalide")
        if transaction.buyer_actor_id != payload.payer_actor_id:
            raise bad_request("transaction_invalide")

    if payload.external_ref:
        existing = db.query(PaymentRequest).filter_by(external_ref=payload.external_ref).first()
        if existing:
            payment = (
                db.query(Payment).filter_by(payment_request_id=existing.id).first()
            )
            return PaymentInitiateResponse(
                payment_request_id=existing.id,
                payment_id=payment.id if payment else 0,
                status=existing.status,
                external_ref=existing.external_ref,
            )

    external_ref = payload.external_ref or uuid4().hex
    request = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=payload.payer_actor_id,
        payee_actor_id=payload.payee_actor_id,
        fee_id=fee.id if fee else None,
        transaction_id=transaction.id if transaction else None,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
        external_ref=external_ref,
        idempotency_key=payload.idempotency_key,
        beneficiary_label=None,
        beneficiary_msisdn=None,
    )
    db.add(request)
    db.flush()
    payment = Payment(payment_request_id=request.id, status="pending")
    db.add(payment)
    db.commit()
    write_audit(
        db,
        actor_id=payload.payer_actor_id,
        action="payment_initiated",
        entity_type="payment_request",
        entity_id=str(request.id),
        meta={"external_ref": request.external_ref, "amount": str(request.amount)},
    )
    db.commit()

    return PaymentInitiateResponse(
        payment_request_id=request.id,
        payment_id=payment.id,
        status=request.status,
        external_ref=request.external_ref,
    )


@router.post("/webhooks/{provider_code}")
async def webhook(provider_code: str, request: Request, db: Session = Depends(get_db)):
    provider = db.query(PaymentProvider).filter_by(code=provider_code).first()
    if not provider:
        raise bad_request("provider_inconnu")

    if settings.webhook_shared_secret:
        secret = request.headers.get("X-Webhook-Secret")
        if secret != settings.webhook_shared_secret:
            raise bad_request("webhook_non_autorise")

    if settings.webhook_ip_allowlist:
        allowed = {ip.strip() for ip in settings.webhook_ip_allowlist.split(",") if ip.strip()}
        client_ip = request.client.host if request.client else ""
        if allowed and client_ip not in allowed:
            raise bad_request("webhook_non_autorise")

    payload = await request.json()
    try:
        parsed = WebhookPayload(**payload)
    except Exception:
        raise bad_request("payload_invalide")

    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    existing = (
        db.query(WebhookInbox)
        .filter_by(provider_id=provider.id, external_ref=parsed.external_ref)
        .first()
    )
    if existing:
        return {"status": "ok", "idempotent": True}

    inbox = WebhookInbox(
        provider_id=provider.id,
        external_ref=parsed.external_ref,
        payload_hash=payload_hash,
        status="received",
    )
    db.add(inbox)

    payment_request = db.query(PaymentRequest).filter_by(external_ref=parsed.external_ref).first()
    if payment_request:
        payment_request.status = parsed.status
        payment = db.query(Payment).filter_by(payment_request_id=payment_request.id).first()
        if payment:
            payment.status = parsed.status
            payment.operator_ref = parsed.operator_ref
            if parsed.status == "success":
                payment.confirmed_at = datetime.now(timezone.utc)
        if parsed.status == "success" and payment_request.fee_id:
            fee = db.query(Fee).filter_by(id=payment_request.fee_id).first()
            if fee and fee.status != "paid":
                fee.status = "paid"
                fee.paid_at = datetime.now(timezone.utc)
                allocate_collector_card_fee_split(db, fee)
                _sync_card_status_after_fee_paid(db, fee.id)
                _ensure_fee_receipt_document(db, fee, payment_request)
                actor = db.query(Actor).filter_by(id=fee.actor_id).first()
                if actor and actor.status == "pending":
                    activation_mode = _get_signup_activation_mode(db)
                    if activation_mode == "auto" and _has_minimal_signup_controls(actor):
                        actor.status = "active"
                write_audit(
                    db,
                    actor_id=fee.actor_id,
                    action="fee_paid",
                    entity_type="fee",
                    entity_id=str(fee.id),
                    meta={"payment_request_id": payment_request.id},
                )
        if parsed.status == "success" and payment_request.transaction_id:
            transaction = (
                db.query(TradeTransaction)
                .filter_by(id=payment_request.transaction_id)
                .first()
            )
            if transaction and transaction.status not in {"paid", "transferred"}:
                _finalize_transaction_success(db, transaction, payment_request)
                write_audit(
                    db,
                    actor_id=transaction.buyer_actor_id,
                    action="invoice_issued",
                    entity_type="transaction",
                    entity_id=str(transaction.id),
                    meta={"transaction_id": transaction.id},
                )
        if parsed.status == "success":
            write_audit(
                db,
                actor_id=payment_request.payer_actor_id,
                action="payment_success",
                entity_type="payment_request",
                entity_id=str(payment_request.id),
                meta={"external_ref": payment_request.external_ref},
            )

    db.commit()
    return {"status": "ok", "idempotent": False}


@router.get("", response_model=list[PaymentRequestOut])
def list_payments(
    payer_actor_id: int | None = None,
    payee_actor_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(PaymentRequest)
    if not _is_admin(db, current_actor.id):
        query = query.filter(
            (PaymentRequest.payer_actor_id == current_actor.id)
            | (PaymentRequest.payee_actor_id == current_actor.id)
        )
        if payer_actor_id and payer_actor_id != current_actor.id:
            return []
        if payee_actor_id and payee_actor_id != current_actor.id:
            return []
    if payer_actor_id:
        query = query.filter(PaymentRequest.payer_actor_id == payer_actor_id)
    if payee_actor_id:
        query = query.filter(PaymentRequest.payee_actor_id == payee_actor_id)
    if status:
        query = query.filter(PaymentRequest.status == status)
    payments = query.order_by(PaymentRequest.created_at.desc()).all()
    return [
        PaymentRequestOut(
            id=p.id,
            provider_id=p.provider_id,
            payer_actor_id=p.payer_actor_id,
            payee_actor_id=p.payee_actor_id,
            fee_id=p.fee_id,
            transaction_id=p.transaction_id,
            amount=float(p.amount),
            currency=p.currency,
            status=p.status,
            external_ref=p.external_ref,
            beneficiary_label=p.beneficiary_label,
            beneficiary_msisdn=p.beneficiary_msisdn,
        )
        for p in payments
    ]


@router.get("/{payment_id}", response_model=PaymentRequestOut)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    payment = db.query(PaymentRequest).filter_by(id=payment_id).first()
    if not payment:
        raise bad_request("paiement_introuvable")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (payment.payer_actor_id, payment.payee_actor_id):
            raise bad_request("acces_refuse")
    return PaymentRequestOut(
        id=payment.id,
        provider_id=payment.provider_id,
        payer_actor_id=payment.payer_actor_id,
        payee_actor_id=payment.payee_actor_id,
        fee_id=payment.fee_id,
        transaction_id=payment.transaction_id,
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status,
        external_ref=payment.external_ref,
        beneficiary_label=payment.beneficiary_label,
        beneficiary_msisdn=payment.beneficiary_msisdn,
    )


@router.get("/status/{external_ref}", response_model=PaymentRequestOut)
def get_payment_status(
    external_ref: str,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    payment = db.query(PaymentRequest).filter_by(external_ref=external_ref).first()
    if not payment:
        raise bad_request("paiement_introuvable")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (payment.payer_actor_id, payment.payee_actor_id):
            raise bad_request("acces_refuse")
    return PaymentRequestOut(
        id=payment.id,
        provider_id=payment.provider_id,
        payer_actor_id=payment.payer_actor_id,
        payee_actor_id=payment.payee_actor_id,
        fee_id=payment.fee_id,
        transaction_id=payment.transaction_id,
        amount=float(payment.amount),
        currency=payment.currency,
        status=payment.status,
        external_ref=payment.external_ref,
        beneficiary_label=payment.beneficiary_label,
        beneficiary_msisdn=payment.beneficiary_msisdn,
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


def _get_signup_activation_mode(db: Session) -> str:
    cfg = db.query(SystemConfig).filter(SystemConfig.key == "signup_activation_mode").first()
    value = (cfg.value or "").strip().lower() if cfg else ""
    if value in {"manual_commune", "manual"}:
        return "manual_commune"
    return "auto"


def _has_minimal_signup_controls(actor: Actor) -> bool:
    return bool(actor.region_id and actor.district_id and actor.commune_id and actor.signup_geo_point_id)


def _sync_card_status_after_fee_paid(db: Session, fee_id: int) -> None:
    for card in db.query(KaraBolamenaCard).filter(KaraBolamenaCard.fee_id == fee_id).all():
        if (card.status or "").lower() == "pending":
            card.status = "pending_validation"
    for card in db.query(CollectorCard).filter(CollectorCard.fee_id == fee_id).all():
        if (card.status or "").lower() == "pending":
            card.status = "pending_validation"


def _ensure_fee_receipt_document(db: Session, fee: Fee, payment_request: PaymentRequest) -> None:
    if fee.receipt_document_id and fee.receipt_number:
        return
    now = datetime.now(timezone.utc)
    receipt_number = build_receipt_number(fee.id, now)
    lines = [
        f"Recu: {receipt_number}",
        f"Frais: {fee.fee_type}",
        f"Acteur payeur: {fee.actor_id}",
        f"Commune beneficiaire: {fee.commune_id}",
        f"Montant: {float(fee.amount):.2f} {fee.currency}",
        f"Canal: {payment_request.provider_id}",
        f"Reference externe: {payment_request.external_ref}",
        f"Date confirmation: {now.isoformat()}",
    ]
    content = build_simple_pdf("MADAVOLA - Recu paiement", lines)
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{receipt_number}.pdf"
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    doc = Document(
        doc_type="receipt",
        owner_actor_id=fee.actor_id,
        related_entity_type="fee",
        related_entity_id=str(fee.id),
        storage_path=str(storage_path),
        original_filename=filename,
        sha256=sha256,
    )
    db.add(doc)
    db.flush()
    fee.receipt_number = receipt_number
    fee.receipt_document_id = doc.id


def _transaction_context(db: Session, transaction: TradeTransaction) -> dict:
    items = (
        db.query(TradeTransactionItem)
        .filter(TradeTransactionItem.transaction_id == transaction.id)
        .all()
    )
    lots = (
        db.query(Lot)
        .filter(Lot.id.in_([item.lot_id for item in items if item.lot_id is not None]))
        .all()
    ) if items else []
    lot_by_id = {lot.id: lot for lot in lots}

    filieres = sorted({(lot.filiere or "").upper() for lot in lots if lot.filiere})
    filiere = filieres[0] if len(filieres) == 1 else (filieres[0] if filieres else "OR")
    lot_refs = []
    origin_refs = []
    units = []
    qty_total = 0.0
    for item in items:
        qty_total += float(item.quantity)
        lot = lot_by_id.get(item.lot_id) if item.lot_id is not None else None
        if lot:
            lot_refs.append(lot.lot_number or f"LOT-{lot.id}")
            if lot.origin_reference:
                origin_refs.append(lot.origin_reference)
            if lot.unit:
                units.append(lot.unit)
    origin_reference = origin_refs[0] if origin_refs else None
    if len(set(origin_refs)) > 1:
        origin_reference = "MIXED_ORIGIN"
    unit = units[0] if len(set(units)) == 1 and units else ("mixed" if units else None)

    seller = db.query(Actor).filter_by(id=transaction.seller_actor_id).first()
    region_code = None
    if seller and seller.region_id:
        region = db.query(Region).filter_by(id=seller.region_id).first()
        region_code = region.code if region else None

    taxes = (
        db.query(TaxRecord)
        .filter(TaxRecord.transaction_id == transaction.id)
        .order_by(TaxRecord.id.asc())
        .all()
    )
    tax_rows = [
        {
            "id": row.id,
            "tax_type": row.tax_type,
            "beneficiary_level": row.beneficiary_level,
            "beneficiary_key": row.beneficiary_key,
            "rate": float(row.tax_rate),
            "amount": float(row.tax_amount),
            "currency": row.currency,
            "status": row.status,
        }
        for row in taxes
    ]
    taxes_total = round(sum(x["amount"] for x in tax_rows), 2)
    subtotal_ht = float(transaction.total_amount)
    total_ttc = round(subtotal_ht + taxes_total, 2)
    unit_price_avg = round(subtotal_ht / qty_total, 2) if qty_total > 0 else None

    return {
        "filiere": filiere,
        "region_code": region_code,
        "origin_reference": origin_reference,
        "lot_refs": lot_refs,
        "quantity_total": qty_total,
        "unit": unit,
        "unit_price_avg": unit_price_avg,
        "subtotal_ht": subtotal_ht,
        "tax_rows": tax_rows,
        "taxes_total": taxes_total,
        "total_ttc": total_ttc,
    }


def _compute_invoice_chain(db: Session, transaction: TradeTransaction, context: dict, now: datetime) -> dict:
    previous = (
        db.query(Invoice)
        .filter(Invoice.transaction_id != transaction.id)
        .order_by(Invoice.issue_date.desc(), Invoice.id.desc())
        .first()
    )
    previous_hash = previous.invoice_hash if previous and previous.invoice_hash else "GENESIS"
    payload = {
        "transaction_id": transaction.id,
        "seller_actor_id": transaction.seller_actor_id,
        "buyer_actor_id": transaction.buyer_actor_id,
        "filiere": context["filiere"],
        "region_code": context["region_code"],
        "origin_reference": context["origin_reference"],
        "lot_refs": context["lot_refs"],
        "subtotal_ht": context["subtotal_ht"],
        "taxes": context["tax_rows"],
        "total_ttc": context["total_ttc"],
        "previous_invoice_hash": previous_hash,
        "issued_at": now.isoformat(),
    }
    invoice_hash = sha256_hex(canonical_json(payload))
    signing_secret = settings.card_qr_signing_secret or settings.jwt_secret
    signature = sign_hmac_sha256(signing_secret, invoice_hash)
    return {
        "previous_hash": previous_hash,
        "invoice_hash": invoice_hash,
        "signature": signature,
        "payload": payload,
    }


def _ensure_invoice_receipt_document(
    db: Session,
    *,
    invoice: Invoice,
    transaction: TradeTransaction,
    payment_request: PaymentRequest,
    now: datetime,
) -> None:
    if invoice.receipt_document_id and invoice.receipt_number:
        return
    receipt_number = build_receipt_number(invoice.id, now=now)
    receipt_pdf = build_simple_pdf(
        "MADAVOLA - Recu transaction",
        [
            f"Recu: {receipt_number}",
            f"Facture: {invoice.invoice_number}",
            f"Transaction: {transaction.id}",
            f"Paiement externe: {payment_request.external_ref}",
            f"Payeur: {payment_request.payer_actor_id}",
            f"Beneficiaire: {payment_request.payee_actor_id}",
            f"Montant TTC: {float(invoice.total_ttc or transaction.total_amount):.2f} {payment_request.currency}",
            f"Hash facture: {invoice.invoice_hash or '-'}",
            f"Date confirmation: {now.isoformat()}",
        ],
    )
    receipt_filename = f"{receipt_number}.pdf"
    receipt_path = Path(settings.document_storage_dir) / receipt_filename
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(receipt_pdf)
    doc = Document(
        doc_type="receipt",
        owner_actor_id=payment_request.payer_actor_id,
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


def _finalize_transaction_success(db: Session, transaction: TradeTransaction, payment_request: PaymentRequest) -> None:
    transaction.status = "paid"
    now = datetime.now(timezone.utc)
    context = _transaction_context(db, transaction)
    chain = _compute_invoice_chain(db, transaction, context, now)
    existing_invoice = db.query(Invoice).filter(Invoice.transaction_id == transaction.id).first()
    invoice = existing_invoice
    if not invoice:
        invoice_number = build_invoice_number(
            transaction.id,
            filiere=context["filiere"],
            region_code=context["region_code"],
            now=now,
        )
        invoice = Invoice(
            invoice_number=invoice_number,
            transaction_id=transaction.id,
            seller_actor_id=transaction.seller_actor_id,
            buyer_actor_id=transaction.buyer_actor_id,
            total_amount=transaction.total_amount,
            status="paid",
            qr_code=build_qr_value("invoice", invoice_number),
            filiere=context["filiere"],
            region_code=context["region_code"],
            origin_reference=context["origin_reference"],
            lot_references_json=json.dumps(context["lot_refs"], ensure_ascii=True),
            quantity_total=context["quantity_total"],
            unit=context["unit"],
            unit_price_avg=context["unit_price_avg"],
            subtotal_ht=context["subtotal_ht"],
            taxes_json=json.dumps(context["tax_rows"], ensure_ascii=True),
            taxes_total=context["taxes_total"],
            total_ttc=context["total_ttc"],
            previous_invoice_hash=chain["previous_hash"],
            invoice_hash=chain["invoice_hash"],
            internal_signature=chain["signature"],
            trace_payload_json=canonical_json(chain["payload"]),
            is_immutable=True,
        )
        db.add(invoice)
        db.flush()
        invoice_pdf = build_simple_pdf(
            "MADAVOLA - Facture transaction",
            [
                f"Facture: {invoice_number}",
                f"Transaction: {transaction.id}",
                f"Vendeur: {transaction.seller_actor_id}",
                f"Acheteur: {transaction.buyer_actor_id}",
                f"Filiere: {context['filiere']}",
                f"Origine: {context['origin_reference'] or '-'}",
                f"Lots: {', '.join(context['lot_refs']) if context['lot_refs'] else '-'}",
                f"Quantite: {context['quantity_total']:.4f} {context['unit'] or '-'}",
                f"Total HT: {context['subtotal_ht']:.2f} {transaction.currency}",
                f"Taxes: {context['taxes_total']:.2f} {transaction.currency}",
                f"Total TTC: {context['total_ttc']:.2f} {transaction.currency}",
                f"Hash facture: {chain['invoice_hash']}",
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
                owner_actor_id=transaction.seller_actor_id,
                related_entity_type="invoice",
                related_entity_id=str(invoice.id),
                storage_path=str(invoice_path),
                original_filename=invoice_filename,
                sha256=hashlib.sha256(invoice_pdf).hexdigest(),
            )
        )
    else:
        invoice.status = "paid"
        if invoice.filiere is None:
            invoice.filiere = context["filiere"]
        if invoice.region_code is None:
            invoice.region_code = context["region_code"]
        if invoice.origin_reference is None:
            invoice.origin_reference = context["origin_reference"]
        if not invoice.lot_references_json:
            invoice.lot_references_json = json.dumps(context["lot_refs"], ensure_ascii=True)
        if invoice.quantity_total is None:
            invoice.quantity_total = context["quantity_total"]
        if invoice.unit is None:
            invoice.unit = context["unit"]
        if invoice.unit_price_avg is None:
            invoice.unit_price_avg = context["unit_price_avg"]
        if invoice.subtotal_ht is None:
            invoice.subtotal_ht = context["subtotal_ht"]
        if invoice.taxes_json is None:
            invoice.taxes_json = json.dumps(context["tax_rows"], ensure_ascii=True)
        if invoice.taxes_total is None:
            invoice.taxes_total = context["taxes_total"]
        if invoice.total_ttc is None:
            invoice.total_ttc = context["total_ttc"]
        if invoice.previous_invoice_hash is None:
            invoice.previous_invoice_hash = chain["previous_hash"]
        if invoice.invoice_hash is None:
            invoice.invoice_hash = chain["invoice_hash"]
        if invoice.internal_signature is None:
            invoice.internal_signature = chain["signature"]
        if invoice.trace_payload_json is None:
            invoice.trace_payload_json = canonical_json(chain["payload"])
        invoice.is_immutable = True
    _ensure_invoice_receipt_document(
        db,
        invoice=invoice,
        transaction=transaction,
        payment_request=payment_request,
        now=now,
    )
    _apply_transaction_lot_transfer(db, transaction)
    transaction.status = "transferred"


def _apply_transaction_lot_transfer(db: Session, transaction: TradeTransaction) -> None:
    items = (
        db.query(TradeTransactionItem)
        .filter(TradeTransactionItem.transaction_id == transaction.id)
        .all()
    )
    for item in items:
        if not item.lot_id:
            continue
        lot = db.query(Lot).filter(Lot.id == item.lot_id).first()
        if not lot:
            continue
        if lot.current_owner_actor_id != transaction.seller_actor_id:
            continue
        qty = float(item.quantity)
        lot_qty = float(lot.quantity)
        if qty <= 0:
            continue
        if qty >= lot_qty:
            lot.current_owner_actor_id = transaction.buyer_actor_id
            lot.status = "available"
            moved_qty = lot.quantity
            moved_lot_id = lot.id
        else:
            lot.quantity = lot_qty - qty
            child = Lot(
                filiere=lot.filiere,
                product_type=lot.product_type,
                unit=lot.unit,
                quantity=qty,
                declared_by_actor_id=lot.declared_by_actor_id,
                current_owner_actor_id=transaction.buyer_actor_id,
                status="available",
                declare_geo_point_id=lot.declare_geo_point_id,
                parent_lot_id=lot.id,
                notes=lot.notes,
                photo_urls_json=lot.photo_urls_json,
                qr_code=build_qr_value("lot", f"child-{transaction.id}-{lot.id}"),
            )
            db.add(child)
            db.flush()
            moved_qty = qty
            moved_lot_id = child.id
        db.add(
            InventoryLedger(
                actor_id=transaction.seller_actor_id,
                lot_id=moved_lot_id,
                movement_type="transfer_out",
                quantity_delta=-moved_qty,
                ref_event_type="transaction_payment",
                ref_event_id=str(transaction.id),
            )
        )
        db.add(
            InventoryLedger(
                actor_id=transaction.buyer_actor_id,
                lot_id=moved_lot_id,
                movement_type="transfer_in",
                quantity_delta=moved_qty,
                ref_event_type="transaction_payment",
                ref_event_id=str(transaction.id),
            )
        )
