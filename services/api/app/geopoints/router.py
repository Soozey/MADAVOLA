from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
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


@router.get("/{geo_point_id}", response_model=GeoPointOut)
def get_geo_point(
    geo_point_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    point = db.query(GeoPoint).filter_by(id=geo_point_id).first()
    if not point:
        raise bad_request("gps_introuvable")
    if point.actor_id and point.actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    return GeoPointOut(
        id=point.id,
        lat=float(point.lat),
        lon=float(point.lon),
        accuracy_m=point.accuracy_m,
        captured_at=point.captured_at,
        source=point.source,
        device_id=point.device_id,
    )
