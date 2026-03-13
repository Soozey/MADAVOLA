import json

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
    return [_to_invoice_out(inv) for inv in invoices]


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
    return _to_invoice_out(invoice)


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


def _parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
        return loaded if isinstance(loaded, list) else []
    except Exception:
        return []


def _to_invoice_out(inv: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=inv.id,
        invoice_number=inv.invoice_number,
        transaction_id=inv.transaction_id,
        seller_actor_id=inv.seller_actor_id,
        buyer_actor_id=inv.buyer_actor_id,
        issue_date=inv.issue_date,
        filiere=inv.filiere,
        region_code=inv.region_code,
        origin_reference=inv.origin_reference,
        lot_references=[str(x) for x in _parse_json_list(inv.lot_references_json)],
        quantity_total=float(inv.quantity_total) if inv.quantity_total is not None else None,
        unit=inv.unit,
        unit_price_avg=float(inv.unit_price_avg) if inv.unit_price_avg is not None else None,
        subtotal_ht=float(inv.subtotal_ht) if inv.subtotal_ht is not None else None,
        taxes=_parse_json_list(inv.taxes_json),
        taxes_total=float(inv.taxes_total) if inv.taxes_total is not None else None,
        total_ttc=float(inv.total_ttc) if inv.total_ttc is not None else None,
        total_amount=float(inv.total_amount),
        status=inv.status,
        qr_code=inv.qr_code,
        invoice_hash=inv.invoice_hash,
        previous_invoice_hash=inv.previous_invoice_hash,
        internal_signature=inv.internal_signature,
        receipt_number=inv.receipt_number,
        receipt_document_id=inv.receipt_document_id,
    )
