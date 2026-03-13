from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text

from app.models.base import Base


class MarketplaceOffer(Base):
    __tablename__ = "marketplace_offers"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    offer_type = Column(String(20), nullable=False)  # sell|buy
    filiere = Column(String(20), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"))
    product_type = Column(String(60), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="MGA")
    location_commune_id = Column(Integer, ForeignKey("communes.id"))
    status = Column(String(20), nullable=False, default="active")  # active|closed|cancelled
    expires_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
