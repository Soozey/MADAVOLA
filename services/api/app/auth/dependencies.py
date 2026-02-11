from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.db import get_db
from app.models.actor import Actor, ActorRole
from app.auth.security import decode_token
from app.auth.roles_config import has_permission

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_actor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Actor:
    if not credentials:
        raise bad_request("token_manquant")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise bad_request("token_invalide")
    actor_id = int(payload["sub"])
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor or actor.status != "active":
        raise bad_request("compte_inactif")
    return actor


def get_optional_actor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Actor | None:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise bad_request("token_invalide")
    actor_id = int(payload["sub"])
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor or actor.status != "active":
        raise bad_request("compte_inactif")
    return actor


def require_roles(roles: set[str]):
    def _checker(
        actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)
    ) -> Actor:
        now = datetime.now(timezone.utc)
        matches = (
            db.query(ActorRole)
            .filter(ActorRole.actor_id == actor.id)
            .filter(ActorRole.role.in_(roles))
            .filter(ActorRole.status == "active")
            .filter((ActorRole.valid_from == None) | (ActorRole.valid_from <= now))
            .filter((ActorRole.valid_to == None) | (ActorRole.valid_to >= now))
            .first()
        )
        if not matches:
            raise bad_request("role_insuffisant", {"roles": sorted(roles)})
        return actor

    return _checker


def get_actor_role_codes(actor: Actor, db: Session) -> list[str]:
    """Retourne la liste des codes de rôles actifs de l'acteur."""
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor.id)
        .filter(ActorRole.status == "active")
        .filter((ActorRole.valid_from == None) | (ActorRole.valid_from <= now))
        .filter((ActorRole.valid_to == None) | (ActorRole.valid_to >= now))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def require_permission(permission: str):
    """Exige que l'acteur ait au moins un rôle possédant la permission donnée."""

    def _checker(
        actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)
    ) -> Actor:
        role_codes = get_actor_role_codes(actor, db)
        if not has_permission(role_codes, permission):
            raise bad_request("permission_insuffisante", {"permission": permission})
        return actor

    return _checker
