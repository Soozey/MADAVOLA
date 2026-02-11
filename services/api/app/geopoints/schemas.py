from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GeoPointCreate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    accuracy_m: int = Field(gt=0)
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
