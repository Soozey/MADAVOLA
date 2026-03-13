from datetime import date, datetime

from pydantic import BaseModel, Field


class TariffCreate(BaseModel):
    card_type: str
    commune_id: int | None = None
    amount: float = Field(gt=0)
    min_amount: float | None = None
    max_amount: float | None = None
    effective_from: datetime
    effective_to: datetime | None = None


class TariffOut(BaseModel):
    id: int
    card_type: str
    commune_id: int | None = None
    amount: float
    min_amount: float | None = None
    max_amount: float | None = None
    effective_from: datetime
    effective_to: datetime | None = None
    status: str


class KaraCardCreate(BaseModel):
    actor_id: int
    commune_id: int
    cin: str
    nationality: str = "mg"
    residence_verified: bool = False
    tax_compliant: bool = False
    zone_allowed: bool = True
    public_order_clear: bool = True
    notes: str | None = None


class KaraCardDecision(BaseModel):
    decision: str  # approved|rejected|suspended|withdrawn
    notes: str | None = None


class KaraCardOut(BaseModel):
    id: int
    actor_id: int
    commune_id: int
    card_uid: str | None = None
    card_number: str | None = None
    filiere: str = "OR"
    role: str = "orpailleur"
    unique_identifier: str
    status: str
    cin: str
    nationality: str
    residence_verified: bool
    tax_compliant: bool
    zone_allowed: bool
    public_order_clear: bool
    fee_id: int | None = None
    issued_at: datetime | None = None
    validated_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    qr_value: str | None = None
    qr_payload_hash: str | None = None
    qr_signature: str | None = None
    front_document_id: int | None = None
    back_document_id: int | None = None


class ProductionLogCreate(BaseModel):
    card_id: int
    log_date: date
    zone_name: str
    quantity_gram: float = Field(gt=0)
    notes: str | None = None


class ProductionLogOut(BaseModel):
    id: int
    card_id: int
    log_date: date
    zone_name: str
    quantity_gram: float
    notes: str | None = None


class CollectorCardCreate(BaseModel):
    actor_id: int
    issuing_commune_id: int
    notes: str | None = None


class CollectorCardDecision(BaseModel):
    decision: str  # approved|rejected|suspended|withdrawn
    notes: str | None = None


class CollectorDocumentAttach(BaseModel):
    doc_type: str
    document_id: int


class CollectorAffiliationCreate(BaseModel):
    collector_card_id: int
    affiliate_actor_id: int
    affiliate_type: str  # comptoir|bijouterie
    agreement_ref: str
    signed_at: datetime


class CollectorCardOut(BaseModel):
    id: int
    actor_id: int
    issuing_commune_id: int
    card_uid: str | None = None
    card_number: str | None = None
    filiere: str = "OR"
    role: str = "collecteur"
    status: str
    fee_id: int | None = None
    issued_at: datetime | None = None
    validated_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    affiliation_deadline_at: datetime | None = None
    affiliation_submitted_at: datetime | None = None
    laissez_passer_blocked_reason: str | None = None
    qr_value: str | None = None
    qr_payload_hash: str | None = None
    qr_signature: str | None = None
    front_document_id: int | None = None
    back_document_id: int | None = None


class ComptoirLicenseCreate(BaseModel):
    actor_id: int
    cahier_des_charges_ref: str | None = None


class ComptoirLicenseStatusPatch(BaseModel):
    status: str | None = None
    dtspm_status: str | None = None
    fx_repatriation_status: str | None = None
    notes: str | None = None


class ComptoirLicenseOut(BaseModel):
    id: int
    actor_id: int
    status: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    dtspm_status: str
    fx_repatriation_status: str
    access_sig_oc_suspended: bool
    cahier_des_charges_ref: str | None = None
    notes: str | None = None


class ReminderRunOut(BaseModel):
    created_notifications: int


class CardQueueItemOut(BaseModel):
    card_id: int
    card_type: str
    actor_id: int
    commune_id: int
    status: str
    fee_id: int | None = None
    fee_status: str | None = None
    created_at: datetime
    actor_name: str | None = None


class MyCardsOut(BaseModel):
    kara_cards: list[KaraCardOut]
    collector_cards: list[CollectorCardOut]


class CardRequestIn(BaseModel):
    card_type: str  # kara_bolamena|collector_card|bijoutier_card
    actor_id: int
    commune_id: int
    cin: str | None = None
    notes: str | None = None


class CardDecisionIn(BaseModel):
    decision: str  # approved|rejected|suspended|revoked
    notes: str | None = None
    expires_in_days: int | None = Field(default=365, gt=0, le=3650)


class CardRenderOut(BaseModel):
    card_id: int
    card_type: str
    side: str
    status: str
    card_number: str | None = None
    document_id: int | None = None
    download_url: str | None = None
    qr_value: str | None = None
    qr_payload_hash: str | None = None
    qr_signature: str | None = None
