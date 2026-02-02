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
