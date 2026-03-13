from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), nullable=False, unique=True)
    transaction_id = Column(Integer, ForeignKey("trade_transactions.id"), nullable=False)
    seller_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    buyer_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    total_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), nullable=False, default="issued")
    qr_code = Column(String(255), unique=True)
    filiere = Column(String(20))
    region_code = Column(String(20))
    origin_reference = Column(String(160))
    lot_references_json = Column(Text)
    quantity_total = Column(Numeric(14, 4))
    unit = Column(String(20))
    unit_price_avg = Column(Numeric(14, 2))
    subtotal_ht = Column(Numeric(14, 2))
    taxes_json = Column(Text)
    taxes_total = Column(Numeric(14, 2))
    total_ttc = Column(Numeric(14, 2))
    invoice_hash = Column(String(64))
    previous_invoice_hash = Column(String(64))
    internal_signature = Column(String(64))
    trace_payload_json = Column(Text)
    receipt_number = Column(String(80))
    receipt_document_id = Column(Integer, ForeignKey("documents.id"))
    is_immutable = Column(Boolean, nullable=False, default=True)
