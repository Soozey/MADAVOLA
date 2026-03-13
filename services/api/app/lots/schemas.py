from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LotCreate(BaseModel):
    filiere: str = "OR"
    sous_filiere: str | None = None
    product_catalog_id: int | None = None
    wood_essence_id: int | None = None
    wood_form: str | None = None
    volume_m3: float | None = None
    attributes: dict | None = None
    product_type: str
    unit: str
    quantity: float = Field(gt=0)
    declare_geo_point_id: int
    declared_by_actor_id: int
    notes: str | None = None
    photo_urls: list[str] = []
    document_ids: list[int] = []

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        return value


class LotOut(BaseModel):
    id: int
    filiere: str
    sous_filiere: str | None = None
    product_catalog_id: int | None = None
    wood_essence_id: int | None = None
    wood_form: str | None = None
    volume_m3: float | None = None
    attributes: dict | None = None
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
    lot_number: str | None = None
    traceability_id: str | None = None
    origin_reference: str | None = None
    previous_block_hash: str | None = None
    current_block_hash: str | None = None
    wood_classification: str | None = None
    cites_laf_status: str | None = None
    cites_ndf_status: str | None = None
    cites_international_status: str | None = None
    destruction_status: str | None = None
    destruction_requested_at: datetime | None = None
    destruction_validated_at: datetime | None = None
    destruction_evidence_urls: list[str] = []


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


class LotWoodClassificationPatch(BaseModel):
    wood_classification: str | None = None
    cites_laf_status: str | None = None
    cites_ndf_status: str | None = None
    cites_international_status: str | None = None
    destruction_status: str | None = None
    destruction_evidence_urls: list[str] | None = None
    notes: str | None = None
