from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.fees.schemas import FeeCreate, FeeOut
from app.models.actor import Actor
from app.models.fee import Fee
from app.models.territory import Commune

router = APIRouter(prefix=f"{settings.api_prefix}/fees", tags=["fees"])


@router.post("", response_model=FeeOut, status_code=201)
def create_fee(payload: FeeCreate, db: Session = Depends(get_db)):
    actor = db.query(Actor).filter_by(id=payload.actor_id).first()
    if not actor:
        raise bad_request("acteur_invalide")
    commune = db.query(Commune).filter_by(id=payload.commune_id).first()
    if not commune:
        raise bad_request("commune_invalide")

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
    )


@router.get("", response_model=list[FeeOut])
def list_fees(actor_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Fee)
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
        )
        for fee in fees
    ]
