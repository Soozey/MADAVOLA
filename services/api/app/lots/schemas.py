from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LotCreate(BaseModel):
    filiere: str = "OR"
    product_type: str
    unit: str
    quantity: float = Field(gt=0)
    declare_geo_point_id: int
    declared_by_actor_id: int
    notes: str | None = None
    photo_urls: list[str] = []

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        allowed = {"g", "kg", "akotry"}
        if value not in allowed:
            raise ValueError("unite_non_autorisee")
        return value


class LotOut(BaseModel):
    id: int
    filiere: str
    product_type: str
    unit: str
    quantity: float
    declared_at: datetime
    declared_by_actor_id: int
    current_owner_actor_id: int
    status: str
    declare_geo_point_id: int
    notes: str | None = None
    photo_urls: list[str] = []
    qr_code: str | None = None
    declaration_receipt_number: str | None = None
    declaration_receipt_document_id: int | None = None


class LotTransfer(BaseModel):
    new_owner_actor_id: int
    payment_request_id: int


class LotConsolidate(BaseModel):
    lot_ids: list[int]
    product_type: str
    unit: str
    declare_geo_point_id: int


class LotSplit(BaseModel):
    quantities: list[float]
