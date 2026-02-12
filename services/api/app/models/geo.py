...
...
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class GeoPoint(Base):
    __tablename__ = "geo_points"

    id = Column(Integer, primary_key=True)
    lat = Column(Numeric(9, 6), nullable=False)
    lon = Column(Numeric(9, 6), nullable=False)
    accuracy_m = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    source = Column(String(20), nullable=False, default="gps")
    device_id = Column(String(100))
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=True)

    # actor relationship removed temporarily due to ambiguous foreign key issue
    # Can be re-added later with proper foreign_keys specification if needed
