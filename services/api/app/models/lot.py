from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True)
    filiere = Column(String(20), nullable=False, default="OR")
    product_type = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    declared_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    declared_by_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    current_owner_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    status = Column(String(20), nullable=False, default="available")
    declare_geo_point_id = Column(Integer, ForeignKey("geo_points.id"), nullable=False)
    parent_lot_id = Column(Integer, ForeignKey("lots.id"))

    parent = relationship("Lot", remote_side=[id])


class LotLink(Base):
    __tablename__ = "lot_links"

    id = Column(Integer, primary_key=True)
    parent_lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    child_lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    relation_type = Column(String(20), nullable=False)
    quantity_from_child = Column(Numeric(14, 4), nullable=False)


class InventoryLedger(Base):
    __tablename__ = "inventory_ledger"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)
    quantity_delta = Column(Numeric(14, 4), nullable=False)
    ref_event_type = Column(String(50), nullable=False)
    ref_event_id = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
