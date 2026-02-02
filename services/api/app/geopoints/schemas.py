from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GeoPointCreate(BaseModel):
    lat: float
    lon: float
    accuracy_m: int
    captured_at: Optional[datetime] = None
    source: str = "gps"
    device_id: Optional[str] = None


class GeoPointOut(BaseModel):
    id: int
    lat: float
    lon: float
    accuracy_m: int
    captured_at: datetime
    source: str
    device_id: Optional[str] = None
