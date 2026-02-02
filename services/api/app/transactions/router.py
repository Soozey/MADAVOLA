from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.transactions.schemas import TransactionCreate, TransactionOut

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
