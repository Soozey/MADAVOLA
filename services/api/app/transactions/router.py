from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.payment import Payment, PaymentProvider, PaymentRequest
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.transactions.schemas import (
    TransactionCreate,
    TransactionOut,
    TransactionDetailOut,
    TransactionItemOut,
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


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    seller_actor_id: int | None = None,
    buyer_actor_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(TradeTransaction)
    if not _is_admin(db, current_actor.id):
        query = query.filter(
            (TradeTransaction.seller_actor_id == current_actor.id)
            | (TradeTransaction.buyer_actor_id == current_actor.id)
        )
        if seller_actor_id and seller_actor_id != current_actor.id:
            return []
        if buyer_actor_id and buyer_actor_id != current_actor.id:
            return []
    if seller_actor_id:
        query = query.filter(TradeTransaction.seller_actor_id == seller_actor_id)
    if buyer_actor_id:
        query = query.filter(TradeTransaction.buyer_actor_id == buyer_actor_id)
    if status:
        query = query.filter(TradeTransaction.status == status)
    transactions = query.order_by(TradeTransaction.created_at.desc()).all()
    return [
        TransactionOut(
            id=txn.id,
            seller_actor_id=txn.seller_actor_id,
            buyer_actor_id=txn.buyer_actor_id,
            status=txn.status,
            total_amount=float(txn.total_amount),
            currency=txn.currency,
        )
        for txn in transactions
    ]


@router.get("/{transaction_id}", response_model=TransactionDetailOut)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    transaction = (
        db.query(TradeTransaction)
        .filter(TradeTransaction.id == transaction_id)
        .first()
    )
    if not transaction:
        raise bad_request("transaction_introuvable")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (transaction.seller_actor_id, transaction.buyer_actor_id):
            raise bad_request("acces_refuse")
    items = (
        db.query(TradeTransactionItem)
        .filter(TradeTransactionItem.transaction_id == transaction.id)
        .all()
    )
    return TransactionDetailOut(
        id=transaction.id,
        seller_actor_id=transaction.seller_actor_id,
        buyer_actor_id=transaction.buyer_actor_id,
        status=transaction.status,
        total_amount=float(transaction.total_amount),
        currency=transaction.currency,
        items=[
            TransactionItemOut(
                id=item.id,
                lot_id=item.lot_id,
                quantity=float(item.quantity),
                unit_price=float(item.unit_price),
                line_amount=float(item.line_amount),
            )
            for item in items
        ],
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


@router.post("/{transaction_id}/initiate-payment", response_model=TransactionPaymentOut, status_code=201)
def initiate_transaction_payment(
    transaction_id: int,
    payload: TransactionPaymentInitiate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    transaction = db.query(TradeTransaction).filter_by(id=transaction_id).first()
    if not transaction or transaction.status != "pending_payment":
        raise bad_request("transaction_invalide")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (transaction.seller_actor_id, transaction.buyer_actor_id):
            raise bad_request("acces_refuse")

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


@router.get("/{transaction_id}/payments", response_model=list[TransactionPaymentOut])
def list_transaction_payments(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    transaction = db.query(TradeTransaction).filter_by(id=transaction_id).first()
    if not transaction:
        raise bad_request("transaction_introuvable")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (transaction.seller_actor_id, transaction.buyer_actor_id):
            raise bad_request("acces_refuse")
    payments = (
        db.query(PaymentRequest)
        .filter(PaymentRequest.transaction_id == transaction.id)
        .order_by(PaymentRequest.created_at.desc())
        .all()
    )
    payment_map = {
        p.payment_request_id: p.id
        for p in db.query(Payment).filter(Payment.payment_request_id.in_([r.id for r in payments])).all()
    } if payments else {}
    return [
        TransactionPaymentOut(
            payment_request_id=p.id,
            payment_id=payment_map.get(p.id, 0),
            status=p.status,
            external_ref=p.external_ref,
        )
        for p in payments
    ]
