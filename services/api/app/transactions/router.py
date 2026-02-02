from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.payment import Payment, PaymentProvider, PaymentRequest
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.transactions.schemas import (
    TransactionCreate,
    TransactionOut,
    TransactionPaymentInitiate,
    TransactionPaymentOut,
)

router = APIRouter(prefix=f"{settings.api_prefix}/transactions", tags=["transactions"])


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    seller = db.query(Actor).filter_by(id=payload.seller_actor_id).first()
    buyer = db.query(Actor).filter_by(id=payload.buyer_actor_id).first()
    if not seller or not buyer:
        raise bad_request("acteur_invalide")
    if not payload.items:
        raise bad_request("items_obligatoires")

    total = Decimal("0.00")
    items = []
    for item in payload.items:
        qty = Decimal(str(item.quantity))
        unit = Decimal(str(item.unit_price))
        line_amount = qty * unit
        total += line_amount
        items.append((item, line_amount))

    transaction = TradeTransaction(
        seller_actor_id=payload.seller_actor_id,
        buyer_actor_id=payload.buyer_actor_id,
        status="pending_payment",
        total_amount=total,
        currency=payload.currency,
    )
    db.add(transaction)
    db.flush()
    for item, line_amount in items:
        db.add(
            TradeTransactionItem(
                transaction_id=transaction.id,
                lot_id=item.lot_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_amount=line_amount,
            )
        )
    db.commit()
    db.refresh(transaction)
    return TransactionOut(
        id=transaction.id,
        seller_actor_id=transaction.seller_actor_id,
        buyer_actor_id=transaction.buyer_actor_id,
        status=transaction.status,
        total_amount=float(transaction.total_amount),
        currency=transaction.currency,
    )


@router.post("/{transaction_id}/initiate-payment", response_model=TransactionPaymentOut, status_code=201)
def initiate_transaction_payment(
    transaction_id: int,
    payload: TransactionPaymentInitiate,
    db: Session = Depends(get_db),
):
    transaction = db.query(TradeTransaction).filter_by(id=transaction_id).first()
    if not transaction or transaction.status != "pending_payment":
        raise bad_request("transaction_invalide")

    provider = db.query(PaymentProvider).filter_by(code=payload.provider_code).first()
    if not provider or not provider.enabled:
        raise bad_request("provider_indisponible")

    if payload.external_ref:
        existing = db.query(PaymentRequest).filter_by(external_ref=payload.external_ref).first()
        if existing:
            payment = (
                db.query(Payment).filter_by(payment_request_id=existing.id).first()
            )
            return TransactionPaymentOut(
                payment_request_id=existing.id,
                payment_id=payment.id if payment else 0,
                status=existing.status,
                external_ref=existing.external_ref,
            )

    external_ref = payload.external_ref or f"txn-{transaction_id}"
    request = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=transaction.buyer_actor_id,
        payee_actor_id=transaction.seller_actor_id,
        transaction_id=transaction.id,
        amount=transaction.total_amount,
        currency=transaction.currency,
        status="pending",
        external_ref=external_ref,
        idempotency_key=payload.idempotency_key,
    )
    db.add(request)
    db.flush()
    payment = Payment(payment_request_id=request.id, status="pending")
    db.add(payment)
    db.commit()
    return TransactionPaymentOut(
        payment_request_id=request.id,
        payment_id=payment.id,
        status=request.status,
        external_ref=request.external_ref,
    )
