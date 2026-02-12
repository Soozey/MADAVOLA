from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, get_optional_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.fees.schemas import FeeCreate, FeeOut, FeePaymentInitiate, FeePaymentOut
from app.models.actor import Actor, ActorRole
from app.models.fee import Fee
from app.models.payment import Payment, PaymentProvider, PaymentRequest
from app.models.territory import Commune

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
    commune = db.query(Commune).filter_by(id=payload.commune_id).first()
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

    commune = db.query(Commune).filter_by(id=fee.commune_id).first()
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
    commune = db.query(Commune).filter_by(id=commune_id).first()
    return commune.mobile_money_msisdn if commune else None
