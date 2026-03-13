from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class OrTariffConfig(Base):
    __tablename__ = "or_tariff_configs"

    id = Column(Integer, primary_key=True)
    card_type = Column(String(40), nullable=False)  # kara_bolamena|collector_card|comptoir_license
    commune_id = Column(Integer, ForeignKey("communes.id"))
    amount = Column(Numeric(14, 2), nullable=False)
    min_amount = Column(Numeric(14, 2))
    max_amount = Column(Numeric(14, 2))
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="active")
    configured_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class KaraBolamenaCard(Base):
    __tablename__ = "kara_bolamena_cards"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    commune_id = Column(Integer, ForeignKey("communes.id"), nullable=False)
    card_uid = Column(String(80), unique=True)
    card_number = Column(String(120), unique=True)
    unique_identifier = Column(String(80), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="pending")  # pending|active|expired|suspended|withdrawn|rejected
    nationality = Column(String(30), nullable=False, default="mg")
    cin = Column(String(50), nullable=False)
    residence_verified = Column(Boolean, nullable=False, default=False)
    tax_compliant = Column(Boolean, nullable=False, default=False)
    zone_allowed = Column(Boolean, nullable=False, default=True)
    public_order_clear = Column(Boolean, nullable=False, default=True)
    issued_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    validated_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    issued_at = Column(DateTime(timezone=True))
    validated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    renewed_from_card_id = Column(Integer, ForeignKey("kara_bolamena_cards.id"))
    fee_id = Column(Integer, ForeignKey("fees.id"))
    front_document_id = Column(Integer, ForeignKey("documents.id"))
    back_document_id = Column(Integer, ForeignKey("documents.id"))
    qr_payload_json = Column(Text)
    qr_payload_hash = Column(String(64))
    qr_signature = Column(String(128))
    qr_value = Column(String(255))
    card_version = Column(Integer, nullable=False, default=1)
    carnet_mode = Column(String(20), nullable=False, default="electronic")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class KaraProductionLog(Base):
    __tablename__ = "kara_production_logs"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("kara_bolamena_cards.id"), nullable=False)
    log_date = Column(Date, nullable=False)
    zone_name = Column(String(120), nullable=False)
    quantity_gram = Column(Numeric(14, 4), nullable=False)
    notes = Column(Text)
    submitted_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorCard(Base):
    __tablename__ = "collector_cards"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    issuing_commune_id = Column(Integer, ForeignKey("communes.id"), nullable=False)
    card_uid = Column(String(80), unique=True)
    card_number = Column(String(120), unique=True)
    status = Column(String(20), nullable=False, default="pending")  # pending|active|expired|suspended|withdrawn|rejected
    issued_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    validated_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    issued_at = Column(DateTime(timezone=True))
    validated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    renewed_from_card_id = Column(Integer, ForeignKey("collector_cards.id"))
    fee_id = Column(Integer, ForeignKey("fees.id"))
    front_document_id = Column(Integer, ForeignKey("documents.id"))
    back_document_id = Column(Integer, ForeignKey("documents.id"))
    qr_payload_json = Column(Text)
    qr_payload_hash = Column(String(64))
    qr_signature = Column(String(128))
    qr_value = Column(String(255))
    card_version = Column(Integer, nullable=False, default=1)
    affiliation_deadline_at = Column(DateTime(timezone=True))
    affiliation_submitted_at = Column(DateTime(timezone=True))
    laissez_passer_blocked_reason = Column(String(120))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorCardDocument(Base):
    __tablename__ = "collector_card_documents"

    id = Column(Integer, primary_key=True)
    collector_card_id = Column(Integer, ForeignKey("collector_cards.id"), nullable=False)
    doc_type = Column(String(60), nullable=False)
    required = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="missing")  # missing|uploaded|verified|rejected
    document_id = Column(Integer, ForeignKey("documents.id"))
    verified_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorAffiliationAgreement(Base):
    __tablename__ = "collector_affiliation_agreements"

    id = Column(Integer, primary_key=True)
    collector_card_id = Column(Integer, ForeignKey("collector_cards.id"), nullable=False)
    affiliate_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    affiliate_type = Column(String(30), nullable=False)  # comptoir|bijouterie
    agreement_ref = Column(String(120), nullable=False)
    signed_at = Column(DateTime(timezone=True), nullable=False)
    communicated_to_com_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="submitted")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorRegister(Base):
    __tablename__ = "collector_registers"

    id = Column(Integer, primary_key=True)
    collector_card_id = Column(Integer, ForeignKey("collector_cards.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    register_payload_json = Column(Text, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorSemiAnnualReport(Base):
    __tablename__ = "collector_semiannual_reports"

    id = Column(Integer, primary_key=True)
    collector_card_id = Column(Integer, ForeignKey("collector_cards.id"), nullable=False)
    period_label = Column(String(20), nullable=False)  # YYYY-S1|YYYY-S2
    report_payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="submitted")
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ComptoirLicense(Base):
    __tablename__ = "comptoir_licenses"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending|active|suspended|cancelled|expired
    issued_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    dtspm_status = Column(String(20), nullable=False, default="ok")  # ok|late|suspended|cancelled
    fx_repatriation_status = Column(String(20), nullable=False, default="ok")  # ok|late|suspended
    access_sig_oc_suspended = Column(Boolean, nullable=False, default=False)
    cahier_des_charges_ref = Column(String(120))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CollectorCardFeeSplit(Base):
    __tablename__ = "collector_card_fee_splits"

    id = Column(Integer, primary_key=True)
    fee_id = Column(Integer, ForeignKey("fees.id"), nullable=False)
    beneficiary_type = Column(String(30), nullable=False)  # commune|region|com
    beneficiary_ref = Column(String(80), nullable=False)
    ratio_percent = Column(Numeric(8, 4), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), nullable=False, default="allocated")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ComplianceNotification(Base):
    __tablename__ = "compliance_notifications"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(40), nullable=False)  # kara_card|collector_card|comptoir_license
    entity_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    channel = Column(String(20), nullable=False, default="in_app")  # in_app|email|sms
    days_before = Column(Integer, nullable=False)
    message = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="sent")
    sent_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
