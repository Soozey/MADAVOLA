from datetime import datetime

from pydantic import BaseModel


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    transaction_id: int
    seller_actor_id: int
    buyer_actor_id: int
    issue_date: datetime | None = None
    filiere: str | None = None
    region_code: str | None = None
    origin_reference: str | None = None
    lot_references: list[str] = []
    quantity_total: float | None = None
    unit: str | None = None
    unit_price_avg: float | None = None
    subtotal_ht: float | None = None
    taxes: list[dict] = []
    taxes_total: float | None = None
    total_ttc: float | None = None
    total_amount: float
    status: str
    qr_code: str | None = None
    invoice_hash: str | None = None
    previous_invoice_hash: str | None = None
    internal_signature: str | None = None
    receipt_number: str | None = None
    receipt_document_id: int | None = None
