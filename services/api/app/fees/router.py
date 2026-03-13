import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, get_optional_actor
from app.common.errors import bad_request
from app.common.card_identity import build_receipt_number
from app.common.receipts import build_simple_pdf
from app.core.config import settings
from app.db import get_db
from datetime import datetime, timezone

from app.fees.schemas import FeeActorMarkPaid, FeeCreate, FeeOut, FeePaymentInitiate, FeePaymentOut, FeeStatusUpdate
from app.models.actor import Actor, ActorRole
from app.models.document import Document
from app.models.fee import Fee
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.payment import Payment, PaymentProvider, PaymentRequest
from app.models.territory import Commune, TerritoryVersion
from app.or_compliance.fee_split import allocate_collector_card_fee_split

router = APIRouter(prefix=f"{settings.api_prefix}/fees", tags=["fees"])


@router.post("", response_model=FeeOut, status_code=201)
def create_fee(
    payload: FeeCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id) and not _is_commune_agent(db, current_actor.id):
        raise bad_request("acces_refuse")
    actor = db.query(Actor).filter_by(id=payload.actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")
    commune = _get_active_commune_by_id(db, payload.commune_id)
    if not commune:
        raise bad_request("commune_invalide")
    if _is_commune_agent(db, current_actor.id) and current_actor.commune_id != payload.commune_id:
        raise bad_request("acces_refuse")

    existing = (
        db.query(Fee)
        .filter(
            Fee.actor_id == payload.actor_id,
            Fee.fee_type == payload.fee_type,
            Fee.status == "pending",
        )
        .first()
    )
    if existing:
        raise bad_request("frais_deja_en_attente")

    fee = Fee(
        fee_type=payload.fee_type,
        actor_id=payload.actor_id,
        commune_id=payload.commune_id,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return FeeOut(
        id=fee.id,
        fee_type=fee.fee_type,
        actor_id=fee.actor_id,
        commune_id=fee.commune_id,
        amount=float(fee.amount),
        currency=fee.currency,
        status=fee.status,
        commune_mobile_money_msisdn=commune.mobile_money_msisdn if commune else None,
        receipt_number=fee.receipt_number,
        receipt_document_id=fee.receipt_document_id,
    )


@router.get("", response_model=list[FeeOut])
def list_fees(
    actor_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(Fee)
    if _is_admin(db, current_actor.id):
        pass
    elif _is_commune_agent(db, current_actor.id):
        query = query.filter(Fee.commune_id == current_actor.commune_id)
        if actor_id:
            query = query.filter(Fee.actor_id == actor_id)
    else:
        if actor_id and actor_id != current_actor.id:
            return []
        query = query.filter(Fee.actor_id == current_actor.id)
    if actor_id:
        query = query.filter(Fee.actor_id == actor_id)
    fees = query.order_by(Fee.created_at.desc()).all()
    return [
        FeeOut(
            id=fee.id,
            fee_type=fee.fee_type,
            actor_id=fee.actor_id,
            commune_id=fee.commune_id,
            amount=float(fee.amount),
            currency=fee.currency,
            status=fee.status,
            commune_mobile_money_msisdn=_get_commune_msisdn(db, fee.commune_id),
            receipt_number=fee.receipt_number,
            receipt_document_id=fee.receipt_document_id,
        )
        for fee in fees
    ]


@router.get("/{fee_id}", response_model=FeeOut)
def get_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    fee = db.query(Fee).filter_by(id=fee_id).first()
    if not fee:
        raise bad_request("frais_introuvable")
    if _is_admin(db, current_actor.id):
        pass
    elif _is_commune_agent(db, current_actor.id):
        if fee.commune_id != current_actor.commune_id:
            raise bad_request("acces_refuse")
    else:
        if fee.actor_id != current_actor.id:
            raise bad_request("acces_refuse")
    return FeeOut(
        id=fee.id,
        fee_type=fee.fee_type,
        actor_id=fee.actor_id,
        commune_id=fee.commune_id,
        amount=float(fee.amount),
        currency=fee.currency,
        status=fee.status,
        commune_mobile_money_msisdn=_get_commune_msisdn(db, fee.commune_id),
        receipt_number=fee.receipt_number,
        receipt_document_id=fee.receipt_document_id,
    )


@router.post("/{fee_id}/initiate-payment", response_model=FeePaymentOut, status_code=201)
def initiate_opening_fee_payment(
    fee_id: int,
    payload: FeePaymentInitiate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_optional_actor),
):
    fee = db.query(Fee).filter_by(id=fee_id).first()
    if not fee:
        raise bad_request("frais_introuvable")
    if fee.status != "pending":
        raise bad_request("frais_invalide")
    if current_actor and not _is_admin(db, current_actor.id) and fee.actor_id != current_actor.id:
        raise bad_request("acces_refuse")

    provider = db.query(PaymentProvider).filter_by(code=payload.provider_code).first()
    if not provider or not provider.enabled:
        raise bad_request("provider_indisponible")

    commune = _get_active_commune_by_id(db, fee.commune_id)
    if not commune or not commune.mobile_money_msisdn:
        raise bad_request("beneficiaire_communal_introuvable")

    if payload.external_ref:
        existing = db.query(PaymentRequest).filter_by(external_ref=payload.external_ref).first()
        if existing:
            payment = db.query(Payment).filter_by(payment_request_id=existing.id).first()
            return FeePaymentOut(
                payment_request_id=existing.id,
                payment_id=payment.id if payment else 0,
                status=existing.status,
                external_ref=existing.external_ref,
                beneficiary_label=existing.beneficiary_label,
                beneficiary_msisdn=existing.beneficiary_msisdn,
            )

    external_ref = payload.external_ref or f"fee-{fee.id}"
    request = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=fee.actor_id,
        payee_actor_id=fee.actor_id,
        fee_id=fee.id,
        amount=fee.amount,
        currency=fee.currency,
        status="pending",
        external_ref=external_ref,
        idempotency_key=payload.idempotency_key,
        beneficiary_label=f"Commune {commune.code}",
        beneficiary_msisdn=commune.mobile_money_msisdn,
    )
    db.add(request)
    db.flush()
    payment = Payment(payment_request_id=request.id, status="pending")
    db.add(payment)
    db.commit()
    return FeePaymentOut(
        payment_request_id=request.id,
        payment_id=payment.id,
        status=request.status,
        external_ref=request.external_ref,
        beneficiary_label=request.beneficiary_label,
        beneficiary_msisdn=request.beneficiary_msisdn,
    )


@router.patch("/{fee_id}/status", response_model=FeeOut)
def update_fee_status(
    fee_id: int,
    payload: FeeStatusUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    fee = db.query(Fee).filter_by(id=fee_id).first()
    if not fee:
        raise bad_request("frais_introuvable")
    if not _is_admin(db, current_actor.id) and not _is_commune_agent(db, current_actor.id):
        raise bad_request("acces_refuse")
    if _is_commune_agent(db, current_actor.id) and current_actor.commune_id != fee.commune_id:
        raise bad_request("acces_refuse")

    new_status = (payload.status or "").strip().lower()
    if new_status not in {"pending", "paid", "cancelled"}:
        raise bad_request("frais_invalide")
    fee.status = new_status
    fee.paid_at = datetime.now(timezone.utc) if new_status == "paid" else None
    if new_status == "paid":
        allocate_collector_card_fee_split(db, fee)
        _sync_card_status_after_fee_paid(db, fee.id)
        _ensure_fee_receipt_document(db, fee, actor_id=current_actor.id, payment_ref=None)
    db.commit()
    db.refresh(fee)
    return FeeOut(
        id=fee.id,
        fee_type=fee.fee_type,
        actor_id=fee.actor_id,
        commune_id=fee.commune_id,
        amount=float(fee.amount),
        currency=fee.currency,
        status=fee.status,
        commune_mobile_money_msisdn=_get_commune_msisdn(db, fee.commune_id),
        receipt_number=fee.receipt_number,
        receipt_document_id=fee.receipt_document_id,
    )


@router.post("/{fee_id}/mark-paid", response_model=FeeOut)
def actor_mark_fee_paid(
    fee_id: int,
    payload: FeeActorMarkPaid,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    fee = db.query(Fee).filter_by(id=fee_id).first()
    if not fee:
        raise bad_request("frais_introuvable")
    if fee.actor_id != current_actor.id and not _is_admin(db, current_actor.id):
        raise bad_request("acces_refuse")
    if fee.status == "cancelled":
        raise bad_request("frais_invalide")

    fee.status = "paid"
    fee.paid_at = datetime.now(timezone.utc)
    allocate_collector_card_fee_split(db, fee)
    _sync_card_status_after_fee_paid(db, fee.id)
    _ensure_fee_receipt_document(db, fee, actor_id=current_actor.id, payment_ref=payload.payment_ref)
    db.commit()
    db.refresh(fee)
    return FeeOut(
        id=fee.id,
        fee_type=fee.fee_type,
        actor_id=fee.actor_id,
        commune_id=fee.commune_id,
        amount=float(fee.amount),
        currency=fee.currency,
        status=fee.status,
        commune_mobile_money_msisdn=_get_commune_msisdn(db, fee.commune_id),
        receipt_number=fee.receipt_number,
        receipt_document_id=fee.receipt_document_id,
    )


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]))
        .first()
        is not None
    )


def _is_commune_agent(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == "commune_agent")
        .first()
        is not None
    )


def _get_commune_msisdn(db: Session, commune_id: int) -> str | None:
    commune = _get_active_commune_by_id(db, commune_id)
    return commune.mobile_money_msisdn if commune else None


def _get_active_commune_by_id(db: Session, commune_id: int) -> Commune | None:
    active = db.query(TerritoryVersion).filter_by(status="active").first()
    if not active:
        return None
    return (
        db.query(Commune)
        .filter(Commune.id == commune_id, Commune.version_id == active.id)
        .first()
    )


def _sync_card_status_after_fee_paid(db: Session, fee_id: int) -> None:
    for card in db.query(KaraBolamenaCard).filter(KaraBolamenaCard.fee_id == fee_id).all():
        if (card.status or "").lower() == "pending":
            card.status = "pending_validation"
    for card in db.query(CollectorCard).filter(CollectorCard.fee_id == fee_id).all():
        if (card.status or "").lower() == "pending":
            card.status = "pending_validation"


def _ensure_fee_receipt_document(db: Session, fee: Fee, actor_id: int, payment_ref: str | None) -> None:
    if fee.receipt_document_id and fee.receipt_number:
        return
    now = datetime.now(timezone.utc)
    receipt_number = build_receipt_number(fee.id, now)
    lines = [
        f"Recu: {receipt_number}",
        f"Frais: {fee.fee_type}",
        f"Acteur: {fee.actor_id}",
        f"Commune: {fee.commune_id}",
        f"Montant: {float(fee.amount):.2f} {fee.currency}",
        f"Date paiement: {now.isoformat()}",
        f"Reference paiement: {payment_ref or '-'}",
    ]
    content = build_simple_pdf("MADAVOLA - Recu frais", lines)
    storage_dir = Path(settings.document_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{receipt_number}.pdf"
    storage_path = storage_dir / filename
    storage_path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    document = Document(
        doc_type="receipt",
        owner_actor_id=fee.actor_id,
        related_entity_type="fee",
        related_entity_id=str(fee.id),
        storage_path=str(storage_path),
        original_filename=filename,
        sha256=sha256,
    )
    db.add(document)
    db.flush()
    fee.receipt_number = receipt_number
    fee.receipt_document_id = document.id
