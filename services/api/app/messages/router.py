from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.communication import ContactRequest, DirectMessage
from app.messages.schemas import (
    ContactDecisionIn,
    ContactRequestCreate,
    ContactRequestOut,
    DirectMessageCreate,
    DirectMessageOut,
)

router = APIRouter(prefix=f"{settings.api_prefix}/messages", tags=["messages"])


def _is_admin(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole.id)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(["admin", "dirigeant"]), ActorRole.status == "active")
        .first()
        is not None
    )


def _actor_name(actor: Actor | None) -> str | None:
    if not actor:
        return None
    return f"{actor.nom} {actor.prenoms or ''}".strip()


def _to_contact_out(db: Session, row: ContactRequest) -> ContactRequestOut:
    requester = db.query(Actor).filter(Actor.id == row.requester_actor_id).first()
    target = db.query(Actor).filter(Actor.id == row.target_actor_id).first()
    return ContactRequestOut(
        id=row.id,
        requester_actor_id=row.requester_actor_id,
        target_actor_id=row.target_actor_id,
        status=row.status,
        created_at=row.created_at,
        decided_at=row.decided_at,
        requester_name=_actor_name(requester),
        target_name=_actor_name(target),
    )


def _to_message_out(db: Session, row: DirectMessage) -> DirectMessageOut:
    sender = db.query(Actor).filter(Actor.id == row.sender_actor_id).first()
    receiver = db.query(Actor).filter(Actor.id == row.receiver_actor_id).first()
    return DirectMessageOut(
        id=row.id,
        contact_request_id=row.contact_request_id,
        sender_actor_id=row.sender_actor_id,
        receiver_actor_id=row.receiver_actor_id,
        body=row.body,
        created_at=row.created_at,
        read_at=row.read_at,
        sender_name=_actor_name(sender),
        receiver_name=_actor_name(receiver),
    )


def _accepted_contact_between(db: Session, actor_a: int, actor_b: int) -> ContactRequest | None:
    return (
        db.query(ContactRequest)
        .filter(
            ContactRequest.status == "accepted",
            or_(
                and_(ContactRequest.requester_actor_id == actor_a, ContactRequest.target_actor_id == actor_b),
                and_(ContactRequest.requester_actor_id == actor_b, ContactRequest.target_actor_id == actor_a),
            ),
        )
        .order_by(ContactRequest.id.desc())
        .first()
    )


@router.post("/contacts", response_model=ContactRequestOut, status_code=201)
def create_contact_request(
    payload: ContactRequestCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if payload.target_actor_id == current_actor.id:
        raise bad_request("contact_invalide")
    target = db.query(Actor).filter(Actor.id == payload.target_actor_id).first()
    if not target:
        raise bad_request("acteur_introuvable")
    existing = (
        db.query(ContactRequest)
        .filter(
            or_(
                and_(ContactRequest.requester_actor_id == current_actor.id, ContactRequest.target_actor_id == payload.target_actor_id),
                and_(ContactRequest.requester_actor_id == payload.target_actor_id, ContactRequest.target_actor_id == current_actor.id),
            ),
            ContactRequest.status.in_(["pending", "accepted"]),
        )
        .order_by(ContactRequest.id.desc())
        .first()
    )
    if existing:
        return _to_contact_out(db, existing)
    row = ContactRequest(
        requester_actor_id=current_actor.id,
        target_actor_id=payload.target_actor_id,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_contact_out(db, row)


@router.get("/contacts", response_model=list[ContactRequestOut])
def list_contacts(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(ContactRequest).filter(
        or_(ContactRequest.requester_actor_id == current_actor.id, ContactRequest.target_actor_id == current_actor.id)
    )
    if status:
        query = query.filter(ContactRequest.status == status)
    rows = query.order_by(ContactRequest.created_at.desc()).limit(300).all()
    return [_to_contact_out(db, row) for row in rows]


@router.post("/contacts/{contact_id}/decision", response_model=ContactRequestOut)
def decide_contact_request(
    contact_id: int,
    payload: ContactDecisionIn,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    row = db.query(ContactRequest).filter(ContactRequest.id == contact_id).first()
    if not row:
        raise bad_request("demande_introuvable")
    if row.target_actor_id != current_actor.id:
        raise bad_request("acces_refuse")
    decision = (payload.decision or "").strip().lower()
    if decision not in {"accepted", "rejected"}:
        raise bad_request("decision_invalide")
    row.status = decision
    row.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _to_contact_out(db, row)


@router.post("", response_model=DirectMessageOut, status_code=201)
def send_message(
    payload: DirectMessageCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    receiver = db.query(Actor).filter(Actor.id == payload.receiver_actor_id).first()
    if not receiver:
        raise bad_request("acteur_introuvable")
    if payload.receiver_actor_id == current_actor.id:
        raise bad_request("message_invalide")
    message_body = (payload.body or "").strip()
    if not message_body:
        raise bad_request("message_invalide")
    contact = _accepted_contact_between(db, current_actor.id, payload.receiver_actor_id)
    if not contact and not _is_admin(db, current_actor.id):
        raise bad_request("contact_non_autorise")
    row = DirectMessage(
        contact_request_id=contact.id if contact else None,
        sender_actor_id=current_actor.id,
        receiver_actor_id=payload.receiver_actor_id,
        body=message_body,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_message_out(db, row)


@router.get("", response_model=list[DirectMessageOut])
def list_messages(
    with_actor_id: int | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    query = db.query(DirectMessage).filter(
        or_(DirectMessage.sender_actor_id == current_actor.id, DirectMessage.receiver_actor_id == current_actor.id)
    )
    if with_actor_id:
        query = query.filter(
            or_(
                and_(DirectMessage.sender_actor_id == current_actor.id, DirectMessage.receiver_actor_id == with_actor_id),
                and_(DirectMessage.sender_actor_id == with_actor_id, DirectMessage.receiver_actor_id == current_actor.id),
            )
        )
    rows = query.order_by(DirectMessage.created_at.desc()).limit(500).all()
    return [_to_message_out(db, row) for row in rows]
