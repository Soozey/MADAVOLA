from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.auth.schemas import LoginRequest, RefreshRequest, TokenPair
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorAuth, RefreshToken

router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    actor = (
        db.query(Actor)
        .filter((Actor.email == payload.identifier) | (Actor.telephone == payload.identifier))
        .first()
    )
    if not actor or not actor.auth:
        raise bad_request("identifiants_invalides")
    if actor.status != "active":
        raise bad_request("compte_inactif")
    if not verify_password(payload.password, actor.auth.password_hash):
        raise bad_request("identifiants_invalides")
    if not actor.auth.is_active:
        raise bad_request("auth_desactivee")

    access_token = create_access_token(actor.id)
    refresh_token, token_id, expires_at = create_refresh_token(actor.id)
    db.add(
        RefreshToken(
            actor_id=actor.id,
            token_id=token_id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise bad_request("refresh_invalide")

    token_id = token_payload.get("jti")
    actor_id = int(token_payload.get("sub"))
    stored = db.query(RefreshToken).filter_by(token_id=token_id).first()
    if not stored or stored.revoked_at is not None:
        raise bad_request("refresh_invalide")
    if stored.expires_at < datetime.now(timezone.utc):
        raise bad_request("refresh_expire")

    access_token = create_access_token(actor_id)
    refresh_token, new_token_id, expires_at = create_refresh_token(actor_id)
    stored.revoked_at = datetime.now(timezone.utc)
    db.add(
        RefreshToken(
            actor_id=actor_id,
            token_id=new_token_id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise bad_request("refresh_invalide")
    token_id = token_payload.get("jti")
    stored = db.query(RefreshToken).filter_by(token_id=token_id).first()
    if stored and stored.revoked_at is None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "ok"}


@router.get("/me")
def me(actor: Actor = Depends(get_current_actor)):
    return {
        "id": actor.id,
        "type_personne": actor.type_personne,
        "nom": actor.nom,
        "prenoms": actor.prenoms,
        "telephone": actor.telephone,
        "email": actor.email,
        "status": actor.status,
    }
