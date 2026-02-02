from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.geopoints.schemas import GeoPointCreate, GeoPointOut
from app.models.geo import GeoPoint

router = APIRouter(prefix=f"{settings.api_prefix}/geo-points", tags=["geo"])


@router.post("", response_model=GeoPointOut, status_code=201)
def create_geo_point(payload: GeoPointCreate, db: Session = Depends(get_db)):
    captured_at = payload.captured_at or datetime.now(timezone.utc)
    point = GeoPoint(
        lat=payload.lat,
        lon=payload.lon,
        accuracy_m=payload.accuracy_m,
        captured_at=captured_at,
        source=payload.source,
        device_id=payload.device_id,
    )
    db.add(point)
    db.commit()
    db.refresh(point)
    return GeoPointOut(
        id=point.id,
        lat=float(point.lat),
        lon=float(point.lon),
        accuracy_m=point.accuracy_m,
        captured_at=point.captured_at,
        source=point.source,
        device_id=point.device_id,
    )
