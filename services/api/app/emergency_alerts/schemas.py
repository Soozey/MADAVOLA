from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class EmergencyAlertCreate(BaseModel):
    title: str
    message: str
    severity: Literal["medium", "high", "critical"] = "high"
    target_service: Literal["police", "gendarmerie", "both", "bianco", "environnement", "institutionnel"] = "both"
    filiere: str | None = None
    role_code: str | None = None
    geo_point_id: int | None = None


class EmergencyAlertStatusUpdate(BaseModel):
    status: Literal["acknowledged", "resolved", "rejected"]


class EmergencyAlertOut(BaseModel):
    id: int
    actor_id: int
    target_service: str
    filiere: str | None = None
    role_code: str | None = None
    geo_point_id: int | None = None
    title: str
    message: str
    severity: str
    status: str
    handled_by_actor_id: int | None = None
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
