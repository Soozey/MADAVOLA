from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.models.base import Base


class ExportDossier(Base):
    __tablename__ = "export_dossiers"

    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False, default="draft")
    destination = Column(String(100))
    total_weight = Column(Numeric(14, 4))
    created_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
