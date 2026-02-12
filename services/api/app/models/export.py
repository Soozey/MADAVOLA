from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class ExportDossier(Base):
    __tablename__ = "export_dossiers"

    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False, default="draft")
    dossier_number = Column(String(50), unique=True)
    destination = Column(String(100))
    destination_country = Column(String(100))
    transport_mode = Column(String(50))
    total_weight = Column(Numeric(14, 4))
    declared_value = Column(Numeric(14, 2))
    sealed_qr = Column(String(255))
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lots = relationship("ExportLot", back_populates="export_dossier")


class ExportLot(Base):
    __tablename__ = "export_lots"

    id = Column(Integer, primary_key=True)
    export_dossier_id = Column(Integer, ForeignKey("export_dossiers.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    quantity_in_export = Column(Numeric(14, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    export_dossier = relationship("ExportDossier", back_populates="lots")
