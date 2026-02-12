from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class TradeTransaction(Base):
    __tablename__ = "trade_transactions"

    id = Column(Integer, primary_key=True)
    seller_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    buyer_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending_payment")
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    items = relationship("TradeTransactionItem", back_populates="transaction")


class TradeTransactionItem(Base):
    __tablename__ = "trade_transaction_items"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("trade_transactions.id"), nullable=False)
    lot_id = Column(Integer, nullable=True)
    quantity = Column(Numeric(14, 4), nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    line_amount = Column(Numeric(14, 2), nullable=False)

    transaction = relationship("TradeTransaction", back_populates="items")
