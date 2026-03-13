from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class EssenceCatalog(Base):
    __tablename__ = "essence_catalog"

    id = Column(Integer, primary_key=True)
    code_essence = Column(String(40), nullable=False, unique=True)
    nom = Column(String(150), nullable=False)
    categorie = Column(String(30), nullable=False)  # A_protegee|B_artisanale|C_autre
    export_autorise = Column(Integer, nullable=False, default=1)
    requires_cites = Column(Integer, nullable=False, default=0)
    rules_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class RulePolicy(Base):
    __tablename__ = "rule_policies"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False)
    operation = Column(String(40), nullable=False)  # declaration|transport|transformation|export
    category = Column(String(40))
    code = Column(String(80), nullable=False, unique=True)
    params_json = Column(Text, nullable=False, default="{}")
    reference_texte = Column(String(255))
    legal_todo = Column(String(255))
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ChecklistPolicy(Base):
    __tablename__ = "checklist_policies"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False)
    operation = Column(String(40), nullable=False)
    category = Column(String(40))
    required_doc_types_json = Column(Text, nullable=False, default="[]")
    reference_texte = Column(String(255))
    legal_todo = Column(String(255))
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="active")
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TransportRecord(Base):
    __tablename__ = "transport_records"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False, default="BOIS")
    transporter_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    vehicle_ref = Column(String(120))
    depart_at = Column(DateTime(timezone=True), nullable=False)
    arrivee_estimee_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="planned")
    qr_code = Column(String(255), unique=True)
    notes = Column(Text)
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TransportRecordItem(Base):
    __tablename__ = "transport_record_items"

    id = Column(Integer, primary_key=True)
    transport_record_id = Column(Integer, ForeignKey("transport_records.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class WorkflowApproval(Base):
    __tablename__ = "workflow_approvals"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False)
    workflow_type = Column(String(50), nullable=False)  # export_exception
    entity_type = Column(String(50), nullable=False)  # lot_export_exception
    entity_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending|approved|rejected
    decision_notes = Column(Text)
    reference_texte = Column(String(255))
    legal_todo = Column(String(255))
    requested_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    decided_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    decided_at = Column(DateTime(timezone=True))
