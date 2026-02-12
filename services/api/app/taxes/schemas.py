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
    base_amount: float
    currency: str
    dtspm_total_rate: float
    dtspm_total_amount: float
    redevance: TaxComponentOut
    ristourne: TaxComponentOut


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


class CreateTaxEventIn(BaseModel):
    taxable_event_type: str = Field(min_length=1, max_length=40)
    taxable_event_id: str = Field(min_length=1, max_length=80)
    base_amount: float = Field(gt=0)
    currency: str = Field(default="MGA", min_length=3, max_length=10)
    lot_id: int | None = None
    export_id: int | None = None
    transaction_id: int | None = None
    commune_beneficiary_id: int | None = None
    region_beneficiary_id: int | None = None
    province_beneficiary_id: int | None = None


class CreateTaxEventOut(BaseModel):
    breakdown: TaxBreakdownOut
    records: list[TaxRecordOut]


class TaxStatusPatchIn(BaseModel):
    status: str = Field(pattern="^(DUE|PAID|VOID)$")
