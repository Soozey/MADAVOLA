from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.models.base import Base


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    target_service = Column(String(20), nullable=False, default="both")
    filiere = Column(String(20), nullable=True)
    role_code = Column(String(50), nullable=True)
    geo_point_id = Column(Integer, ForeignKey("geo_points.id"), nullable=True)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="high")
    status = Column(String(20), nullable=False, default="open")
    handled_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

