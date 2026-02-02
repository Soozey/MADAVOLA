from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.invoices.schemas import InvoiceOut
from app.models.invoice import Invoice
from app.models.actor import ActorRole

router = APIRouter(prefix=f"{settings.api_prefix}/invoices", tags=["documents"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    transaction_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Invoice)
    if transaction_id:
        query = query.filter(Invoice.transaction_id == transaction_id)
    invoices = query.order_by(Invoice.issue_date.desc()).all()
    if not _is_admin(db, current_actor.id):
        invoices = [
            inv
            for inv in invoices
            if current_actor.id in (inv.seller_actor_id, inv.buyer_actor_id)
        ]
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


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    invoice = db.query(Invoice).filter_by(id=invoice_id).first()
    if not invoice:
        raise bad_request("facture_introuvable")
    if not _is_admin(db, current_actor.id):
        if current_actor.id not in (invoice.seller_actor_id, invoice.buyer_actor_id):
            raise bad_request("acces_refuse")
    return InvoiceOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        transaction_id=invoice.transaction_id,
        seller_actor_id=invoice.seller_actor_id,
        buyer_actor_id=invoice.buyer_actor_id,
        total_amount=float(invoice.total_amount),
        status=invoice.status,
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )
