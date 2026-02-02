from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    doc_type = Column(String(30), nullable=False)
    owner_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    related_entity_type = Column(String(50))
    related_entity_id = Column(String(50))
    storage_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
