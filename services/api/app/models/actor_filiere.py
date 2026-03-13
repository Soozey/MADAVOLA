from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.models.base import Base


class ActorFiliere(Base):
    __tablename__ = "actor_filieres"
    __table_args__ = (UniqueConstraint("actor_id", "filiere", name="uq_actor_filieres_actor_filiere"),)

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    filiere = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
