from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.invoices.schemas import InvoiceOut
from app.models.invoice import Invoice

router = APIRouter(prefix=f"{settings.api_prefix}/invoices", tags=["documents"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    return [
        InvoiceOut(
            id=inv.id,
            invoice_number=inv.invoice_number,
            transaction_id=inv.transaction_id,
            seller_actor_id=inv.seller_actor_id,
            buyer_actor_id=inv.buyer_actor_id,
            total_amount=float(inv.total_amount),
            status=inv.status,
        )
        for inv in invoices
    ]
