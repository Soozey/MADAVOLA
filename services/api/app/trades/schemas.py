from pydantic import BaseModel


class TradeItemCreate(BaseModel):
    lot_id: int
    quantity: float
    unit_price: float


class TradeCreate(BaseModel):
    seller_actor_id: int
    buyer_actor_id: int
    currency: str = "MGA"
    items: list[TradeItemCreate]


class TradePayIn(BaseModel):
    payment_mode: str = "mobile_money"  # mobile_money|cash_declared
    provider_code: str | None = None
    external_ref: str | None = None
    idempotency_key: str | None = None


class TradeOut(BaseModel):
    id: int
    seller_actor_id: int
    buyer_actor_id: int
    status: str
    total_amount: float
    currency: str
