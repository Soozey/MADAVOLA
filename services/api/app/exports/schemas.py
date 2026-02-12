from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExportCreate(BaseModel):
    destination: str | None = None
    destination_country: str | None = None
    transport_mode: str | None = None
    total_weight: float | None = None
    declared_value: float | None = None


class ExportStatusUpdate(BaseModel):
    status: str


class ExportLotLink(BaseModel):
    lot_id: int
    quantity_in_export: float


class ExportOut(BaseModel):
    id: int
    status: str
    dossier_number: str | None = None
    destination: str | None = None
    destination_country: str | None = None
    transport_mode: str | None = None
    total_weight: float | None = None
    declared_value: float | None = None
    sealed_qr: str | None = None
    created_by_actor_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
