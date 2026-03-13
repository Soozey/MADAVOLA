from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class ProductCatalog(Base):
    __tablename__ = "product_catalog"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    nom = Column(String(150), nullable=False)
    famille = Column(String(60), nullable=False, default="PIERRE")
    filiere = Column(String(20), nullable=False, default="PIERRE")
    sous_filiere = Column(String(30), nullable=False)  # GEMME|INDUSTRIELLE
    allowed_units_json = Column(Text, nullable=False, default="[]")
    required_attributes_json = Column(Text, nullable=False, default="[]")
    export_restricted = Column(Integer, nullable=False, default=0)
    export_rules_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ActorAuthorization(Base):
    __tablename__ = "actor_authorizations"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    filiere = Column(String(20), nullable=False, default="PIERRE")
    authorization_type = Column(String(40), nullable=False)
    numero = Column(String(120), nullable=False, unique=True)
    issued_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class FeePolicy(Base):
    __tablename__ = "fee_policies"

    id = Column(Integer, primary_key=True)
    code = Column(String(80), nullable=False, unique=True)
    filiere = Column(String(20), nullable=False, default="PIERRE")
    sous_filiere = Column(String(30))
    commune_id = Column(Integer, ForeignKey("communes.id"))
    role_code = Column(String(60))
    fee_type = Column(String(50), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    legal_reference = Column(String(255))
    legal_todo = Column(String(255))
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ExportColis(Base):
    __tablename__ = "export_colis"

    id = Column(Integer, primary_key=True)
    export_dossier_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    package_code = Column(String(80), nullable=False, unique=True)
    gross_weight = Column(Numeric(14, 4), nullable=False)
    net_weight = Column(Numeric(14, 4), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ExportSeal(Base):
    __tablename__ = "export_seals"

    id = Column(Integer, primary_key=True)
    export_dossier_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    seal_number = Column(String(120), nullable=False, unique=True)
    pv_document_id = Column(Integer, ForeignKey("documents.id"))
    sealed_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    sealed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), nullable=False, default="active")


class ExportValidationStep(Base):
    __tablename__ = "export_validation_steps"

    id = Column(Integer, primary_key=True)
    export_dossier_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    step_code = Column(String(50), nullable=False)  # mines|douanes
    validator_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    decision = Column(String(20), nullable=False)  # approved|rejected
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class PierreTransformationEvent(Base):
    __tablename__ = "pierre_transformation_events"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    operation_type = Column(String(40), nullable=False)  # tri|lavage|taille|polissage|split|consolidation
    sous_filiere = Column(String(30), nullable=False)
    loss_ratio = Column(Numeric(10, 6), nullable=False, default=0)
    notes = Column(Text)
    document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class PierreTransformationLink(Base):
    __tablename__ = "pierre_transformation_links"

    id = Column(Integer, primary_key=True)
    transformation_event_id = Column(Integer, ForeignKey("pierre_transformation_events.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    link_type = Column(String(10), nullable=False)  # input|output
    quantity = Column(Numeric(14, 4), nullable=False)
