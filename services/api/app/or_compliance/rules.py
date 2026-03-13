from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.actor import Actor, ActorRole
from app.models.or_compliance import CollectorCard, KaraBolamenaCard


def _now() -> datetime:
    return datetime.now(timezone.utc)


def actor_has_role(db: Session, actor_id: int, roles: set[str]) -> bool:
    return (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role.in_(roles), ActorRole.status == "active")
        .first()
        is not None
    )


def get_active_kara_card(db: Session, actor_id: int) -> KaraBolamenaCard | None:
    now = _now()
    return (
        db.query(KaraBolamenaCard)
        .filter(
            KaraBolamenaCard.actor_id == actor_id,
            KaraBolamenaCard.status.in_(["active", "validated"]),
            KaraBolamenaCard.expires_at != None,  # noqa: E711
            KaraBolamenaCard.expires_at > now,
        )
        .order_by(KaraBolamenaCard.expires_at.desc())
        .first()
    )


def get_active_collector_cards(db: Session, actor_id: int) -> list[CollectorCard]:
    now = _now()
    return (
        db.query(CollectorCard)
        .filter(
            CollectorCard.actor_id == actor_id,
            CollectorCard.status.in_(["active", "validated"]),
            CollectorCard.expires_at != None,  # noqa: E711
            CollectorCard.expires_at > now,
        )
        .all()
    )


def ensure_affiliation_deadlines(db: Session, actor_id: int) -> None:
    now = _now()
    cards = get_active_collector_cards(db, actor_id)
    late = False
    for card in cards:
        deadline = card.affiliation_deadline_at
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if deadline and deadline < now and not card.affiliation_submitted_at:
            card.laissez_passer_blocked_reason = "affiliation_non_communiquee"
            late = True
        else:
            card.laissez_passer_blocked_reason = None
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if actor:
        actor.laissez_passer_access_status = "blocked" if late else "active"


def can_declare_or_lot(db: Session, actor_id: int) -> tuple[bool, str | None]:
    if actor_has_role(db, actor_id, {"orpailleur"}):
        if not get_active_kara_card(db, actor_id):
            return False, "kara_bolamena_invalide"
    if actor_has_role(db, actor_id, {"collecteur", "bijoutier"}):
        cards = get_active_collector_cards(db, actor_id)
        if not cards:
            return False, "carte_collecteur_invalide"
        ensure_affiliation_deadlines(db, actor_id)
        actor = db.query(Actor).filter_by(id=actor_id).first()
        if actor and actor.laissez_passer_access_status != "active":
            return False, "laissez_passer_bloque"
    return True, None


def can_trade_or(db: Session, seller_actor_id: int, buyer_actor_id: int) -> tuple[bool, str | None]:
    seller_actor = db.query(Actor).filter_by(id=seller_actor_id).first()
    buyer_actor = db.query(Actor).filter_by(id=buyer_actor_id).first()
    if not seller_actor or not buyer_actor:
        return False, "acteur_invalide"

    seller_ok, seller_reason = can_declare_or_lot(db, seller_actor_id)
    if not seller_ok:
        return False, seller_reason
    buyer_ok, buyer_reason = can_declare_or_lot(db, buyer_actor_id)
    if actor_has_role(db, buyer_actor_id, {"collecteur", "bijoutier"}) and not buyer_ok:
        return False, buyer_reason
    return True, None
