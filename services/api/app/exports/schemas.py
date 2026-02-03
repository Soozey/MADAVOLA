from datetime import datetime

from pydantic import BaseModel


class ExportCreate(BaseModel):
    destination: str | None = None
    total_weight: float | None = None


class ExportStatusUpdate(BaseModel):
    status: str


class ExportLotLink(BaseModel):
    lot_id: int
    quantity_in_export: float


class ExportOut(BaseModel):
    id: int
    status: str
    destination: str | None = None
    total_weight: float | None = None
    created_by_actor_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True