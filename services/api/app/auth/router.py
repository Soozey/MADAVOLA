from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor
from app.auth.schemas import (
    ActorProfile,
    ActorProfilePatch,
    ActorRoleInfo,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TerritoryInfo,
    TokenPair,
)
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.audit.logger import write_audit
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorAuth, RefreshToken
from app.models.actor_filiere import ActorFiliere
from app.models.territory import Commune, District, Fokontany, Region

router = APIRouter(prefix=f"{settings.api_prefix}/auth", tags=["auth"])

ROLE_PRIORITY = (
    "admin",
    "dirigeant",
    "com_admin",
    "com_agent",
    "com",
    "commune_agent",
    "commune",
)


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
    actor.auth.last_login_at = datetime.now(timezone.utc)
    db.add(
        RefreshToken(
            actor_id=actor.id,
            token_id=token_id,
            expires_at=expires_at,
        )
    )
    db.commit()
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=bool(actor.auth.must_change_password),
    )


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
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
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
    active_roles = [
        (role.role or "").strip().lower()
        for role in actor.roles
        if (role.status or "active").strip().lower() == "active"
    ]
    if not active_roles:
        active_roles = [(role.role or "").strip().lower() for role in actor.roles if (role.role or "").strip()]
    primary_role = None
    for code in ROLE_PRIORITY:
        if code in active_roles:
            primary_role = code
            break
    if primary_role is None and active_roles:
        primary_role = active_roles[0]
    filieres = [
        row[0]
        for row in (
            db.query(ActorFiliere.filiere)
            .filter(ActorFiliere.actor_id == actor.id)
            .order_by(ActorFiliere.filiere.asc())
            .all()
        )
        if row[0]
    ]
    if not filieres:
        filieres = ["OR"]

    return ActorProfile(
        id=actor.id,
        type_personne=actor.type_personne,
        nom=actor.nom,
        prenoms=actor.prenoms,
        surnom=actor.surnom,
        telephone=actor.telephone,
        email=actor.email,
        status=actor.status,
        cin=actor.cin,
        cin_date_delivrance=actor.cin_date_delivrance,
        date_naissance=actor.date_naissance,
        adresse_text=actor.adresse_text,
        photo_profile_url=actor.photo_profile_url,
        nif=actor.nif,
        stat=actor.stat,
        rccm=actor.rccm,
        region=region_info,
        district=district_info,
        commune=commune_info,
        fokontany=fokontany_info,
        roles=roles_info,
        filieres=filieres,
        primary_role=primary_role,
        must_change_password=bool(actor.auth.must_change_password) if actor.auth else False,
        created_at=actor.created_at,
    )


@router.patch("/me", response_model=ActorProfile)
def patch_me(
    payload: ActorProfilePatch,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    today = datetime.now(timezone.utc).date()
    if payload.date_naissance and payload.date_naissance > today:
        raise bad_request("date_naissance_invalide")
    if payload.cin_date_delivrance and payload.cin_date_delivrance > today:
        raise bad_request("cin_date_delivrance_invalide")
    if payload.date_naissance and payload.cin_date_delivrance and payload.cin_date_delivrance < payload.date_naissance:
        raise bad_request("cin_date_delivrance_invalide")

    if payload.nom is not None:
        actor.nom = payload.nom.strip()
    if payload.prenoms is not None:
        actor.prenoms = payload.prenoms.strip() or None
    if payload.date_naissance is not None:
        actor.date_naissance = payload.date_naissance
    if payload.adresse_text is not None:
        actor.adresse_text = payload.adresse_text.strip() or None

    if payload.cin is not None:
        cin_digits = "".join(ch for ch in payload.cin if ch.isdigit())
        if cin_digits and len(cin_digits) != 12:
            raise bad_request("cin_invalide")
        actor.cin = cin_digits or None
    if payload.cin_date_delivrance is not None:
        actor.cin_date_delivrance = payload.cin_date_delivrance

    if payload.commune_code is not None:
        target_commune_code = payload.commune_code.strip().upper()
        if not target_commune_code:
            raise bad_request("commune_invalide")
        commune = db.query(Commune).filter(Commune.code == target_commune_code).first()
        if not commune:
            raise bad_request("commune_invalide")
        district = db.query(District).filter(District.id == commune.district_id).first()
        if not district:
            raise bad_request("district_invalide")
        region = db.query(Region).filter(Region.id == district.region_id).first()
        if not region:
            raise bad_request("region_invalide")
        actor.commune_id = commune.id
        actor.district_id = district.id
        actor.region_id = region.id
        # Reset fokontany when commune changes and no explicit new fokontany is provided.
        if payload.fokontany_code is None:
            actor.fokontany_id = None

    if payload.fokontany_code is not None:
        code = payload.fokontany_code.strip().upper()
        if not code:
            actor.fokontany_id = None
        else:
            commune_id = actor.commune_id
            if not commune_id:
                raise bad_request("commune_invalide")
            fokontany = (
                db.query(Fokontany)
                .filter(Fokontany.code == code, Fokontany.commune_id == commune_id)
                .first()
            )
            if not fokontany:
                raise bad_request("fokontany_invalide")
            actor.fokontany_id = fokontany.id

    db.commit()
    write_audit(
        db,
        actor_id=actor.id,
        action="actor_profile_updated",
        entity_type="actor",
        entity_id=str(actor.id),
        meta={
            "updated_fields": sorted([key for key, value in payload.model_dump(exclude_none=False).items() if value is not None]),
        },
    )
    db.commit()
    return me(actor=actor, db=db)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    auth = db.query(ActorAuth).filter(ActorAuth.actor_id == actor.id).first()
    if not auth or not auth.is_active:
        raise bad_request("auth_desactivee")
    if not verify_password(payload.current_password or "", auth.password_hash):
        raise bad_request("mot_de_passe_actuel_invalide")
    new_password = (payload.new_password or "").strip()
    if len(new_password) < 8:
        raise bad_request("mot_de_passe_trop_court")
    if verify_password(new_password, auth.password_hash):
        raise bad_request("mot_de_passe_identique")

    old_hash = auth.password_hash
    auth.password_hash = hash_password(new_password)
    auth.must_change_password = 0
    auth.password_changed_at = datetime.now(timezone.utc)
    db.commit()
    write_audit(
        db,
        actor_id=actor.id,
        action="password_changed",
        entity_type="actor_auth",
        entity_id=str(auth.id),
        meta={
            "must_change_password_previous": True,
            "must_change_password_next": False,
            "old_hash_prefix": old_hash[:10],
            "new_hash_prefix": auth.password_hash[:10],
        },
    )
    db.commit()
    return {"status": "ok"}
