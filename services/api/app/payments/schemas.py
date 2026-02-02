from pydantic import BaseModel


class PaymentInitiate(BaseModel):
    provider_code: str
    payer_actor_id: int
    payee_actor_id: int
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
