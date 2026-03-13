from datetime import datetime

from pydantic import BaseModel, Field


class LegalVersionCreate(BaseModel):
    filiere: str = "OR"
    legal_key: str = "dtspm"
    version_tag: str
    effective_from: datetime
    effective_to: datetime | None = None
    payload_json: str
    status: str = "active"


class LegalVersionOut(BaseModel):
    id: int
    filiere: str
    legal_key: str
    version_tag: str
    effective_from: datetime
    effective_to: datetime | None
    payload_json: str
    status: str


class LotTestCertificateCreate(BaseModel):
    lot_id: int
    gross_weight: float = Field(gt=0)
    purity: float = Field(gt=0, le=1)


class LotTestCertificateOut(BaseModel):
    id: int
    lot_id: int
    tested_by_actor_id: int
    gross_weight: float
    purity: float
    certificate_number: str
    certificate_qr: str
    status: str
    issued_at: datetime


class TransportEventCreate(BaseModel):
    lot_id: int
    transporter_actor_id: int
    depart_actor_id: int
    arrival_actor_id: int
    depart_geo_point_id: int
    laissez_passer_document_id: int | None = None


class TransportEventArrivalPatch(BaseModel):
    arrival_geo_point_id: int
    status: str = "delivered"


class TransportEventOut(BaseModel):
    id: int
    lot_id: int
    transporter_actor_id: int
    depart_actor_id: int
    arrival_actor_id: int
    depart_geo_point_id: int
    arrival_geo_point_id: int | None
    laissez_passer_document_id: int | None
    depart_at: datetime
    arrival_at: datetime | None
    status: str


class TransformationFacilityCreate(BaseModel):
    facility_type: str
    operator_actor_id: int
    autorisation_ref: str
    valid_from: datetime
    valid_to: datetime
    capacity_declared: float | None = None
    status: str = "active"


class TransformationFacilityOut(BaseModel):
    id: int
    facility_type: str
    operator_actor_id: int
    autorisation_ref: str
    valid_from: datetime
    valid_to: datetime
    capacity_declared: float | None = None
    status: str


class TransformationEventCreate(BaseModel):
    lot_input_id: int
    facility_id: int
    quantity_input: float = Field(gt=0)
    quantity_output: float = Field(gt=0)
    perte_declared: float = Field(ge=0)
    justificatif: str | None = None
    output_product_type: str
    output_unit: str


class TransformationEventOut(BaseModel):
    id: int
    lot_input_id: int
    facility_id: int
    quantity_input: float
    quantity_output: float
    perte_declared: float
    justificatif: str | None = None
    validated_by_actor_id: int | None = None
    output_lot_id: int | None = None
    status: str
    created_at: datetime


class ExportValidationCreate(BaseModel):
    export_id: int
    validator_role: str
    decision: str
    notes: str | None = None


class ExportValidationOut(BaseModel):
    id: int
    export_id: int
    validator_actor_id: int
    validator_role: str
    decision: str
    notes: str | None = None
    created_at: datetime


class ForexRepatriationCreate(BaseModel):
    export_id: int
    amount: float = Field(gt=0)
    currency: str = "USD"
    proof_document_id: int | None = None
    status: str = "validated"


class ForexRepatriationOut(BaseModel):
    id: int
    export_id: int
    bank_actor_id: int
    proof_document_id: int | None = None
    amount: float
    currency: str
    status: str
    repatriated_at: datetime


class ExportChecklistItemOut(BaseModel):
    id: int
    export_id: int
    doc_type: str
    required: int
    status: str
    document_id: int | None = None
    due_at: datetime
    verified_by_actor_id: int | None = None
    verified_at: datetime | None = None
    notes: str | None = None
    is_overdue: bool


class ExportChecklistVerifyIn(BaseModel):
    checklist_item_id: int
    document_id: int
    notes: str | None = None
