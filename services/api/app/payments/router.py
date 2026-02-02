import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.fee import Fee
from app.models.payment import Payment, PaymentProvider, PaymentRequest, WebhookInbox
from app.payments.schemas import PaymentInitiate, PaymentInitiateResponse, WebhookPayload

router = APIRouter(prefix=f"{settings.api_prefix}/payments", tags=["payments"])


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

    db.commit()
    return {"status": "ok", "idempotent": False}
