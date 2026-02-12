from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True)
    inspector_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    inspected_actor_id = Column(Integer, ForeignKey("actors.id"))
    inspected_lot_id = Column(Integer, ForeignKey("lots.id"))
    inspected_invoice_id = Column(Integer, ForeignKey("invoices.id"))
    result = Column(String(20), nullable=False)
    reason_code = Column(String(50))
    notes = Column(String(255))
    geo_point_id = Column(Integer, ForeignKey("geo_points.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ViolationCase(Base):
    __tablename__ = "violation_cases"

    id = Column(Integer, primary_key=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    violation_type = Column(String(50), nullable=False)
    legal_basis_ref = Column(String(100))
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    inspection = relationship("Inspection")


class Penalty(Base):
    __tablename__ = "penalties"

    id = Column(Integer, primary_key=True)
    violation_case_id = Column(Integer, ForeignKey("violation_cases.id"), nullable=False)
    penalty_type = Column(String(50), nullable=False)
    amount = Column(Numeric(14, 2))
    status = Column(String(20), nullable=False, default="open")
    executed_by_actor_id = Column(Integer, ForeignKey("actors.id"))
    executed_at = Column(DateTime(timezone=True))

    violation_case = relationship("ViolationCase")
