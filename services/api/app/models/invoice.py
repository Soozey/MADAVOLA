from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.models.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), nullable=False, unique=True)
    transaction_id = Column(Integer, ForeignKey("trade_transactions.id"), nullable=False)
    seller_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    buyer_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    total_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), nullable=False, default="issued")
