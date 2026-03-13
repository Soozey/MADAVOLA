from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.card_identity import verify_hmac_sha256
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.territory import Commune

router = APIRouter(prefix=f"{settings.api_prefix}/karabola", tags=["karabola"])


class KarabolaCardOut(BaseModel):
    card_id: int
    card_type: str
    actor_id: int
    card_number: str | None = None
    card_uid: str | None = None
    status: str
    commune_id: int | None = None
    validated_at: datetime | None = None
    expires_at: datetime | None = None
    qr_hash: str | None = None


class KarabolaVerifyIn(BaseModel):
    card_ref: str


class KarabolaLinkUserIn(BaseModel):
    card_type: str
    card_id: int
    actor_id: int


def _is_admin_like(db: Session, actor_id: int) -> bool:
    return (
        db.query(ActorRole)
        .filter(
            ActorRole.actor_id == actor_id,
            ActorRole.status == "active",
            ActorRole.role.in_(["admin", "dirigeant", "com_admin", "com_agent", "commune_agent", "commune"]),
        )
        .first()
        is not None
    )


def _display_status(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value == "active":
        return "validated"
    if value == "pending":
        return "pending_payment"
    if value == "withdrawn":
        return "revoked"
    return value or "pending_payment"


def _verify_card_payload(db: Session, card_ref: str) -> dict:
    card_type = "kara_bolamena"
    card = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.card_number == card_ref).first()
    if not card and card_ref.isdigit():
        card = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.id == int(card_ref)).first()
    if not card:
        card_type = "collector_card"
        card = db.query(CollectorCard).filter(CollectorCard.card_number == card_ref).first()
    if not card and card_ref.isdigit():
        card = db.query(CollectorCard).filter(CollectorCard.id == int(card_ref)).first()
        card_type = "collector_card"
    if not card:
        raise bad_request("carte_introuvable")

    actor = db.query(Actor).filter(Actor.id == card.actor_id).first()
    commune_id = card.commune_id if card_type == "kara_bolamena" else card.issuing_commune_id
    commune = db.query(Commune).filter(Commune.id == commune_id).first()
    signing_secret = settings.card_qr_signing_secret or settings.jwt_secret
    signature_valid = False
    if card.qr_payload_hash and card.qr_signature:
        signature_valid = verify_hmac_sha256(signing_secret, card.qr_payload_hash, card.qr_signature)

    status = _display_status(card.status)
    expires_at = card.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= datetime.now(timezone.utc):
        status = "expired"

    return {
        "card_id": card.id,
        "card_type": card_type,
        "card_number": card.card_number,
        "card_uid": card.card_uid,
        "actor_id": card.actor_id,
        "full_name": f"{actor.nom} {actor.prenoms or ''}".strip() if actor else None,
        "commune_code": commune.code if commune else None,
        "status": status,
        "validated_at": card.validated_at,
        "expires_at": card.expires_at,
        "qr_hash": card.qr_payload_hash,
        "signature_valid": signature_valid,
    }


@router.get("", response_model=list[KarabolaCardOut])
def list_karabola_cards(
    actor_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    target_actor_id = actor_id or current_actor.id
    if target_actor_id != current_actor.id and not _is_admin_like(db, current_actor.id):
        raise bad_request("acces_refuse")
    wanted_status = (status or "").strip().lower() or None
    out: list[KarabolaCardOut] = []
    kara_rows = db.query(KaraBolamenaCard).filter(KaraBolamenaCard.actor_id == target_actor_id).all()
    for row in kara_rows:
        display_status = _display_status(row.status)
        if wanted_status and wanted_status != display_status:
            continue
        out.append(
            KarabolaCardOut(
                card_id=row.id,
                card_type="kara_bolamena",
                actor_id=row.actor_id,
                card_number=row.card_number,
                card_uid=row.card_uid,
                status=display_status,
                commune_id=row.commune_id,
                validated_at=row.validated_at,
                expires_at=row.expires_at,
                qr_hash=row.qr_payload_hash,
            )
        )
    collector_rows = db.query(CollectorCard).filter(CollectorCard.actor_id == target_actor_id).all()
    for row in collector_rows:
        display_status = _display_status(row.status)
        if wanted_status and wanted_status != display_status:
            continue
        out.append(
            KarabolaCardOut(
                card_id=row.id,
                card_type="collector_card",
                actor_id=row.actor_id,
                card_number=row.card_number,
                card_uid=row.card_uid,
                status=display_status,
                commune_id=row.issuing_commune_id,
                validated_at=row.validated_at,
                expires_at=row.expires_at,
                qr_hash=row.qr_payload_hash,
            )
        )
    out.sort(key=lambda row: row.card_id, reverse=True)
    return out


@router.post("/verify")
def verify_karabola_card(
    payload: KarabolaVerifyIn,
    db: Session = Depends(get_db),
):
    return _verify_card_payload(db, payload.card_ref.strip())


@router.post("/link-user")
def link_karabola_user(
    payload: KarabolaLinkUserIn,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "com_admin", "commune_agent", "commune"})),
):
    target_actor = db.query(Actor).filter_by(id=payload.actor_id).first()
    if not target_actor:
        raise bad_request("acteur_invalide")
    kind = (payload.card_type or "").strip().lower()
    if kind == "kara_bolamena":
        card = db.query(KaraBolamenaCard).filter_by(id=payload.card_id).first()
    elif kind in {"collector_card", "collector"}:
        kind = "collector_card"
        card = db.query(CollectorCard).filter_by(id=payload.card_id).first()
    else:
        raise bad_request("type_carte_invalide")
    if not card:
        raise bad_request("carte_introuvable")
    card.actor_id = payload.actor_id
    db.commit()
    return {
        "status": "ok",
        "card_type": kind,
        "card_id": payload.card_id,
        "actor_id": payload.actor_id,
    }
