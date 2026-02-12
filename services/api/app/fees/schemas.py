from pydantic import BaseModel


class FeeCreate(BaseModel):
    fee_type: str
    actor_id: int
    commune_id: int
    amount: float
    currency: str = "MGA"


class FeeOut(BaseModel):
    id: int
    fee_type: str
    actor_id: int
    commune_id: int
    amount: float
    currency: str
    status: str
    commune_mobile_money_msisdn: str | None = None


class FeePaymentInitiate(BaseModel):
    provider_code: str
    external_ref: str | None = None
    idempotency_key: str | None = None


class FeePaymentOut(BaseModel):
    payment_request_id: int
    payment_id: int
    status: str
    external_ref: str
    beneficiary_label: str | None = None
    beneficiary_msisdn: str | None = None
