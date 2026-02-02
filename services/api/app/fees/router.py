from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.fees.schemas import FeeCreate, FeeOut
from app.models.actor import Actor, ActorRole
from app.models.fee import Fee
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
        )
        for fee in fees
    ]


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
