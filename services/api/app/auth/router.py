from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.auth.schemas import ActorProfile, ActorRoleInfo, LoginRequest, RefreshRequest, TerritoryInfo, TokenPair
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
from app.models.territory import Commune, District, Fokontany, Region

router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["auth"])


def _normalize_phone_mg(identifier: str) -> str | None:
    """0340000000 -> +261340000000 ; +261340000000 inchangé."""
    s = identifier.strip().replace(" ", "")
    if s.startswith("+261") and len(s) == 12:
        return s
    if s.startswith("261") and len(s) == 11:
        return "+" + s
    if s.startswith("0") and len(s) == 10 and s[1:].isdigit():
        return "+261" + s[1:]
    return None


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = (payload.identifier or "").strip()
    password = (payload.password or "").strip()
    if not identifier or not password:
        raise bad_request("identifiants_invalides")

    conditions = [
        Actor.email == identifier,
        Actor.telephone == identifier,
    ]
    normalized = _normalize_phone_mg(identifier)
    if normalized:
        conditions.append(Actor.telephone == normalized)
    actor = db.query(Actor).filter(or_(*conditions)).first()
    if not actor or not actor.auth:
        raise bad_request("identifiants_invalides")
    if actor.status != "active":
        raise bad_request("compte_inactif")
    if not verify_password(password, actor.auth.password_hash):
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


@router.get("/me", response_model=ActorProfile)
def me(actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
    # Optimize: Load all territory details in a single query using UNION or separate optimized queries
    # Since territories are small, we can load them efficiently
    region_info = None
    district_info = None
    commune_info = None
    fokontany_info = None

    # Load territories in parallel (optimized: single query per type)
    if actor.region_id:
        region = db.query(Region).filter_by(id=actor.region_id).first()
        if region:
            region_info = TerritoryInfo(id=region.id, code=region.code, name=region.name)

    if actor.district_id:
        district = db.query(District).filter_by(id=actor.district_id).first()
        if district:
            district_info = TerritoryInfo(id=district.id, code=district.code, name=district.name)

    if actor.commune_id:
        commune = db.query(Commune).filter_by(id=actor.commune_id).first()
        if commune:
            commune_info = TerritoryInfo(id=commune.id, code=commune.code, name=commune.name)

    if actor.fokontany_id:
        fokontany = db.query(Fokontany).filter_by(id=actor.fokontany_id).first()
        if fokontany:
            fokontany_info = TerritoryInfo(id=fokontany.id, code=fokontany.code or "", name=fokontany.name)

    # Roles are already loaded via relationship (eager loading would be better but requires model change)
    roles_info = [
        ActorRoleInfo(
            id=role.id,
            role=role.role,
            status=role.status,
            valid_from=role.valid_from,
            valid_to=role.valid_to,
        )
        for role in actor.roles
    ]

    return ActorProfile(
        id=actor.id,
        type_personne=actor.type_personne,
        nom=actor.nom,
        prenoms=actor.prenoms,
        telephone=actor.telephone,
        email=actor.email,
        status=actor.status,
        cin=actor.cin,
        nif=actor.nif,
        stat=actor.stat,
        rccm=actor.rccm,
        region=region_info,
        district=district_info,
        commune=commune_info,
        fokontany=fokontany_info,
        roles=roles_info,
        created_at=actor.created_at,
    )
