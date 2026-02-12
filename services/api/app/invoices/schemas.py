from pydantic import BaseModel


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    transaction_id: int
    seller_actor_id: int
    buyer_actor_id: int
    total_amount: float
    status: str
    qr_code: str | None = None
