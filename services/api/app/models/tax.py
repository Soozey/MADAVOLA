from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.models.base import Base


class TaxRecord(Base):
    __tablename__ = "tax_records"

    id = Column(Integer, primary_key=True)
    taxable_event_type = Column(String(40), nullable=False)
    taxable_event_id = Column(String(80), nullable=False)
    tax_type = Column(String(40), nullable=False)
    beneficiary_level = Column(String(20), nullable=False)
    beneficiary_id = Column(Integer)
    beneficiary_key = Column(String(40), nullable=False)
    base_amount = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(12, 8), nullable=False)
    tax_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    lot_id = Column(Integer, ForeignKey("lots.id"))
    export_id = Column(Integer, ForeignKey("export_dossiers.id"))
    transaction_id = Column(Integer, ForeignKey("trade_transactions.id"))
    status = Column(String(20), nullable=False, default="DUE")
    attribution_note = Column(String(120))
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
