from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class TransformationFacility(Base):
    __tablename__ = "transformation_facilities"

    id = Column(Integer, primary_key=True)
    facility_type = Column(String(40), nullable=False)  # raffinerie|atelier_lapidation|atelier_bois|centre_test
    operator_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    autorisation_ref = Column(String(120), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)
    capacity_declared = Column(Numeric(14, 4))
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TransformationEvent(Base):
    __tablename__ = "transformation_events"

    id = Column(Integer, primary_key=True)
    lot_input_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("transformation_facilities.id"), nullable=False)
    quantity_input = Column(Numeric(14, 4), nullable=False)
    quantity_output = Column(Numeric(14, 4), nullable=False)
    perte_declared = Column(Numeric(14, 4), nullable=False, default=0)
    justificatif = Column(Text)
    validated_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    output_lot_id = Column(Integer, ForeignKey("lots.id"))
    status = Column(String(20), nullable=False, default="validated")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LotTestCertificate(Base):
    __tablename__ = "lot_test_certificates"

    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    tested_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    gross_weight = Column(Numeric(14, 4), nullable=False)
    purity = Column(Numeric(8, 4), nullable=False)
    certificate_number = Column(String(80), nullable=False, unique=True)
    certificate_qr = Column(String(255), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="validated")
    issued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TransportEvent(Base):
    __tablename__ = "transport_events"

    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    transporter_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    depart_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    arrival_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    depart_geo_point_id = Column(Integer, ForeignKey("geo_points.id"), nullable=False)
    arrival_geo_point_id = Column(Integer, ForeignKey("geo_points.id"))
    laissez_passer_document_id = Column(Integer, ForeignKey("documents.id"))
    depart_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    arrival_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="in_transit")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ExportValidation(Base):
    __tablename__ = "export_validations"

    id = Column(Integer, primary_key=True)
    export_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    validator_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    validator_role = Column(String(40), nullable=False)  # com|dgd|gue
    decision = Column(String(20), nullable=False)  # approved|rejected
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ForexRepatriation(Base):
    __tablename__ = "forex_repatriations"

    id = Column(Integer, primary_key=True)
    export_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    bank_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    proof_document_id = Column(Integer, ForeignKey("documents.id"))
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="validated")
    repatriated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ExportChecklistItem(Base):
    __tablename__ = "export_checklist_items"

    id = Column(Integer, primary_key=True)
    export_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    doc_type = Column(String(50), nullable=False)
    required = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="missing")  # missing|uploaded|verified
    document_id = Column(Integer, ForeignKey("documents.id"))
    due_at = Column(DateTime(timezone=True), nullable=False)
    verified_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LegalVersioning(Base):
    __tablename__ = "legal_versioning"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False, default="OR")
    legal_key = Column(String(80), nullable=False)  # dtspm
    version_tag = Column(String(40), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TaxBreakdown(Base):
    __tablename__ = "tax_breakdowns"

    id = Column(Integer, primary_key=True)
    taxable_event_type = Column(String(40), nullable=False)
    taxable_event_id = Column(String(80), nullable=False)
    legal_version_id = Column(Integer, ForeignKey("legal_versioning.id"))
    tax_type = Column(String(40), nullable=False)
    beneficiary_level = Column(String(20), nullable=False)
    beneficiary_id = Column(Integer)
    base_amount = Column(Numeric(14, 2), nullable=False)
    tax_rate = Column(Numeric(12, 8), nullable=False)
    tax_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    payment_request_id = Column(Integer, ForeignKey("payment_requests.id"))
    status = Column(String(20), nullable=False, default="DUE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
