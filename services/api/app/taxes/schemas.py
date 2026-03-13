from datetime import datetime

from pydantic import BaseModel, Field


class TaxBeneficiaryOut(BaseModel):
    beneficiary_level: str
    beneficiary_id: int | None = None
    allocation_share: float
    rate_of_base: float
    amount: float
    attribution_note: str | None = None


class TaxComponentOut(BaseModel):
    tax_type: str
    rate: float
    amount: float
    beneficiaries: list[TaxBeneficiaryOut]


class TaxBreakdownOut(BaseModel):
    event_type: str
    base_amount: float
    currency: str
    assiette_mode: str
    assiette_reference: str | None = None
    dtspm_total_rate: float | None = None
    dtspm_total_amount: float | None = None
    abatement_rate: float | None = None
    abatement_reason: str | None = None
    legal_basis: list[str] = []
    redevance: TaxComponentOut | None = None
    ristourne: TaxComponentOut | None = None
    components: list[TaxComponentOut] = []


class TaxRecordOut(BaseModel):
    id: int
    taxable_event_type: str
    taxable_event_id: str
    tax_type: str
    beneficiary_level: str
    beneficiary_id: int | None = None
    base_amount: float
    tax_rate: float
    tax_amount: float
    currency: str
    lot_id: int | None = None
    export_id: int | None = None
    transaction_id: int | None = None
    status: str
    attribution_note: str | None = None


class TaxEventOut(BaseModel):
    id: int
    taxable_event_type: str
    taxable_event_id: str
    anti_double_key: str
    period_key: str | None = None
    reference_transaction: str | None = None
    filiere: str
    region_code: str | None = None
    assiette_mode: str
    assiette_reference: str | None = None
    base_amount: float
    currency: str
    total_amount: float
    abatement_rate: float
    abatement_reason: str | None = None
    legal_basis: list[str] = []
    legal_version_id: int | None = None
    payer_actor_id: int | None = None
    payer_role_code: str | None = None
    lot_id: int | None = None
    export_id: int | None = None
    transaction_id: int | None = None
    status: str
    invoice_number: str | None = None
    invoice_document_id: int | None = None
    receipt_number: str | None = None
    receipt_document_id: int | None = None
    payment_request_id: int | None = None
    created_at: datetime
    updated_at: datetime


class CreateTaxEventIn(BaseModel):
    taxable_event_type: str = Field(min_length=1, max_length=40)
    taxable_event_id: str = Field(min_length=1, max_length=80)
    base_amount: float | None = Field(default=None, gt=0)
    currency: str = Field(default="MGA", min_length=3, max_length=10)
    filiere: str = Field(default="OR", min_length=2, max_length=20)
    region_code: str | None = Field(default=None, max_length=20)
    assiette_mode: str | None = Field(default=None, max_length=30)
    period_key: str | None = Field(default=None, max_length=20)
    reference_transaction: str | None = Field(default=None, max_length=80)
    substance: str | None = Field(default=None, max_length=40)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    local_market_value_id: int | None = None
    local_market_value_override: float | None = Field(default=None, gt=0)
    lot_id: int | None = None
    export_id: int | None = None
    transaction_id: int | None = None
    payer_actor_id: int | None = None
    payer_role_code: str | None = Field(default=None, max_length=60)
    transformed: bool = False
    transformation_origin: str | None = Field(default=None, max_length=40)  # national_refinery|other
    unpaid_upstream_dtspm: bool = False
    legal_key: str | None = Field(default=None, max_length=80)
    commune_beneficiary_id: int | None = None
    region_beneficiary_id: int | None = None
    province_beneficiary_id: int | None = None


class CreateTaxEventOut(BaseModel):
    event: TaxEventOut
    breakdown: TaxBreakdownOut
    records: list[TaxRecordOut]


class TaxStatusPatchIn(BaseModel):
    status: str = Field(pattern="^(DUE|PAID|VOID)$")
    payment_request_id: int | None = None


class LocalMarketValueCreateIn(BaseModel):
    filiere: str = Field(default="OR", min_length=2, max_length=20)
    substance: str = Field(default="OR", min_length=1, max_length=40)
    region_code: str | None = Field(default=None, max_length=20)
    commune_code: str | None = Field(default=None, max_length=20)
    unit: str = Field(default="kg", min_length=1, max_length=20)
    value_per_unit: float = Field(gt=0)
    currency: str = Field(default="MGA", min_length=3, max_length=10)
    legal_reference: str = Field(min_length=3, max_length=255)
    version_tag: str = Field(min_length=1, max_length=40)
    effective_from: datetime
    effective_to: datetime | None = None
    status: str = Field(default="active", pattern="^(active|inactive)$")


class LocalMarketValueOut(BaseModel):
    id: int
    filiere: str
    substance: str
    region_code: str | None = None
    commune_code: str | None = None
    unit: str
    value_per_unit: float
    currency: str
    legal_reference: str
    version_tag: str
    effective_from: datetime
    effective_to: datetime | None = None
    status: str
