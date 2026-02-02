from pydantic import BaseModel


class PaymentInitiate(BaseModel):
    provider_code: str
    payer_actor_id: int
    payee_actor_id: int
    fee_id: int | None = None
    transaction_id: int | None = None
    amount: float
    currency: str
    external_ref: str | None = None
    idempotency_key: str | None = None


class PaymentInitiateResponse(BaseModel):
    payment_request_id: int
    payment_id: int
    status: str
    external_ref: str


class WebhookPayload(BaseModel):
    external_ref: str
    status: str


class PaymentRequestOut(BaseModel):
    id: int
    provider_id: int
    payer_actor_id: int
    payee_actor_id: int
    fee_id: int | None = None
    transaction_id: int | None = None
    amount: float
    currency: str
    status: str
    external_ref: str


class PaymentProviderCreate(BaseModel):
    code: str
    name: str
    enabled: bool = False
    config_json: str | None = None


class PaymentProviderUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    config_json: str | None = None


class PaymentProviderOut(BaseModel):
    id: int
    code: str
    name: str
    enabled: bool
    config_json: str | None = None
