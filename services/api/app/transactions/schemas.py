from pydantic import BaseModel


class TransactionItemCreate(BaseModel):
    lot_id: int | None = None
    quantity: float
    unit_price: float


class TransactionCreate(BaseModel):
    seller_actor_id: int
    buyer_actor_id: int
    currency: str
    items: list[TransactionItemCreate]


class TransactionOut(BaseModel):
    id: int
    seller_actor_id: int
    buyer_actor_id: int
    status: str
    total_amount: float
    currency: str


class TransactionPaymentInitiate(BaseModel):
    provider_code: str
    external_ref: str | None = None
    idempotency_key: str | None = None


class TransactionPaymentOut(BaseModel):
    payment_request_id: int
    payment_id: int
    status: str
    external_ref: str
