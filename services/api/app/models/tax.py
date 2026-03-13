from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text

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


class TaxEventRegistry(Base):
    __tablename__ = "tax_event_registry"

    id = Column(Integer, primary_key=True)
    taxable_event_type = Column(String(40), nullable=False)
    taxable_event_id = Column(String(80), nullable=False)
    anti_double_key = Column(String(96), nullable=False, unique=True)
    period_key = Column(String(20))
    reference_transaction = Column(String(80))
    filiere = Column(String(20), nullable=False, default="OR")
    region_code = Column(String(20))
    assiette_mode = Column(String(30), nullable=False, default="manual")
    assiette_reference = Column(String(160))
    base_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    total_amount = Column(Numeric(14, 2), nullable=False)
    abatement_rate = Column(Numeric(12, 8), nullable=False, default=0)
    abatement_reason = Column(String(180))
    legal_basis_json = Column(Text)
    legal_version_id = Column(Integer, ForeignKey("legal_versioning.id"))
    payer_actor_id = Column(Integer, ForeignKey("actors.id"))
    payer_role_code = Column(String(60))
    lot_id = Column(Integer, ForeignKey("lots.id"))
    export_id = Column(Integer, ForeignKey("export_dossiers.id"))
    transaction_id = Column(Integer, ForeignKey("trade_transactions.id"))
    status = Column(String(20), nullable=False, default="DUE")
    invoice_number = Column(String(80), unique=True)
    invoice_document_id = Column(Integer, ForeignKey("documents.id"))
    receipt_number = Column(String(80), unique=True)
    receipt_document_id = Column(Integer, ForeignKey("documents.id"))
    payment_request_id = Column(Integer, ForeignKey("payment_requests.id"))
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


class LocalMarketValue(Base):
    __tablename__ = "local_market_values"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False, default="OR")
    substance = Column(String(40), nullable=False, default="OR")
    region_code = Column(String(20))
    commune_code = Column(String(20))
    unit = Column(String(20), nullable=False, default="kg")
    value_per_unit = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    legal_reference = Column(String(255), nullable=False)
    version_tag = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
