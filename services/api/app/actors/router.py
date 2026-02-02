from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion
from app.actors.schemas import ActorCreate, ActorOut

router = APIRouter(prefix=f"{settings.api_prefix}/actors", tags=["actors"])


@router.post("", response_model=ActorOut, status_code=201)
def create_actor(payload: ActorCreate, db: Session = Depends(get_db)):
    active_version = db.query(TerritoryVersion).filter_by(status="active").first()
    if not active_version:
        raise bad_request("territoire_non_charge")

    region = (
        db.query(Region)
        .filter(Region.version_id == active_version.id, Region.code == payload.region_code)
        .first()
    )
    district = (
        db.query(District)
        .filter(
            District.version_id == active_version.id,
            District.code == payload.district_code,
            District.region_id == region.id if region else None,
        )
        .first()
        if region
        else None
    )
    commune = (
        db.query(Commune)
        .filter(
            Commune.version_id == active_version.id,
            Commune.code == payload.commune_code,
            Commune.district_id == district.id if district else None,
        )
        .first()
        if district
        else None
    )
    fokontany = None
    if payload.fokontany_code:
        fokontany = (
            db.query(Fokontany)
            .filter(
                Fokontany.version_id == active_version.id,
                Fokontany.code == payload.fokontany_code,
                Fokontany.commune_id == commune.id if commune else None,
            )
            .first()
            if commune
            else None
        )

    if not region or not district or not commune:
        raise bad_request("territoire_invalide")

    geo_point = db.query(GeoPoint).filter_by(id=payload.geo_point_id).first()
    if not geo_point:
        raise bad_request("gps_obligatoire")

    if db.query(Actor).filter(Actor.telephone == payload.telephone).first():
        raise bad_request("telephone_deja_utilise")
    if payload.email and db.query(Actor).filter(Actor.email == payload.email).first():
        raise bad_request("email_deja_utilise")

    actor = Actor(
        type_personne=payload.type_personne,
        nom=payload.nom,
        prenoms=payload.prenoms,
        cin=payload.cin,
        nif=payload.nif,
        stat=payload.stat,
        rccm=payload.rccm,
        telephone=payload.telephone,
        email=payload.email,
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        fokontany_id=fokontany.id if fokontany else None,
        territory_version_id=active_version.id,
        signup_geo_point_id=geo_point.id,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(actor)
    db.flush()
    db.add(ActorAuth(actor_id=actor.id, password_hash=hash_password(payload.password), is_active=1))

    roles = sorted(set(payload.roles))
    if not roles:
        raise bad_request("roles_obligatoires")
    for role in roles:
        db.add(ActorRole(actor_id=actor.id, role=role, status="active"))

    geo_point.actor_id = actor.id
    db.commit()
    db.refresh(actor)
    return ActorOut(
        id=actor.id,
        type_personne=actor.type_personne,
        nom=actor.nom,
        prenoms=actor.prenoms,
        telephone=actor.telephone,
        email=actor.email,
        status=actor.status,
    )
