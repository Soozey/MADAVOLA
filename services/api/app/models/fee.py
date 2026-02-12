from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True)
    fee_type = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    commune_id = Column(Integer, ForeignKey("communes.id"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    paid_at = Column(DateTime(timezone=True))

    payment_requests = relationship("PaymentRequest", back_populates="fee")
