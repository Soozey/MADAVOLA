import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.audit.logger import write_audit
from app.models.actor import Actor
from app.models.fee import Fee
from app.auth.dependencies import require_roles
from app.models.invoice import Invoice
from app.models.payment import Payment, PaymentProvider, PaymentRequest, WebhookInbox
from app.models.transaction import TradeTransaction
from app.payments.providers_schemas import ProviderCreate, ProviderOut, ProviderUpdate
from app.payments.schemas import PaymentInitiate, PaymentInitiateResponse, WebhookPayload

router = APIRouter(prefix=f"{settings.api_prefix}/payments", tags=["payments"])


@router.post("/providers", response_model=ProviderOut, status_code=201)
def create_provider(
    payload: ProviderCreate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    existing = db.query(PaymentProvider).filter_by(code=payload.code).first()
    if existing:
        raise bad_request("provider_existe")
    provider = PaymentProvider(
        code=payload.code,
        name=payload.name,
        enabled=payload.enabled,
        config_json=payload.config_json,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return ProviderOut(
        id=provider.id,
        code=provider.code,
        name=provider.name,
        enabled=provider.enabled,
        config_json=provider.config_json,
    )


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    providers = db.query(PaymentProvider).order_by(PaymentProvider.code.asc()).all()
    return [
        ProviderOut(
            id=p.id,
            code=p.code,
            name=p.name,
            enabled=p.enabled,
            config_json=p.config_json,
        )
        for p in providers
    ]


@router.patch("/providers/{provider_id}", response_model=ProviderOut)
def update_provider(
    provider_id: int,
    payload: ProviderUpdate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    provider = db.query(PaymentProvider).filter_by(id=provider_id).first()
    if not provider:
        raise bad_request("provider_inconnu")
    if payload.name is not None:
        provider.name = payload.name
    if payload.enabled is not None:
        provider.enabled = payload.enabled
    if payload.config_json is not None:
        provider.config_json = payload.config_json
    db.commit()
    db.refresh(provider)
    return ProviderOut(
        id=provider.id,
        code=provider.code,
        name=provider.name,
        enabled=provider.enabled,
        config_json=provider.config_json,
    )

@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=201)
def initiate_payment(payload: PaymentInitiate, db: Session = Depends(get_db)):
    provider = db.query(PaymentProvider).filter_by(code=payload.provider_code).first()
    if not provider or not provider.enabled:
        raise bad_request("provider_indisponible")

    payer = db.query(Actor).filter_by(id=payload.payer_actor_id).first()
    payee = db.query(Actor).filter_by(id=payload.payee_actor_id).first()
    if not payer or not payee:
        raise bad_request("acteur_invalide")

    fee = None
    if payload.fee_id:
        fee = db.query(Fee).filter_by(id=payload.fee_id).first()
        if not fee or fee.status != "pending":
            raise bad_request("frais_invalide")

    transaction = None
    if payload.transaction_id:
        transaction = (
            db.query(TradeTransaction).filter_by(id=payload.transaction_id).first()
        )
        if not transaction or transaction.status != "pending_payment":
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
            if parsed.status == "success":
                payment.confirmed_at = datetime.now(timezone.utc)
        if parsed.status == "success" and payment_request.fee_id:
            fee = db.query(Fee).filter_by(id=payment_request.fee_id).first()
            if fee and fee.status != "paid":
                fee.status = "paid"
                fee.paid_at = datetime.now(timezone.utc)
                actor = db.query(Actor).filter_by(id=fee.actor_id).first()
                if actor and actor.status == "pending":
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
            if transaction and transaction.status != "paid":
                transaction.status = "paid"
                invoice_number = f"INV-{transaction.id:08d}"
                invoice = Invoice(
                    invoice_number=invoice_number,
                    transaction_id=transaction.id,
                    seller_actor_id=transaction.seller_actor_id,
                    buyer_actor_id=transaction.buyer_actor_id,
                    total_amount=transaction.total_amount,
                    status="issued",
                )
                db.add(invoice)
                write_audit(
                    db,
                    actor_id=transaction.buyer_actor_id,
                    action="invoice_issued",
                    entity_type="invoice",
                    entity_id=invoice_number,
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
