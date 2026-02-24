from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, get_optional_actor, require_roles
from app.auth.security import hash_password
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.audit.logger import write_audit
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.actor_filiere import ActorFiliere
from app.models.fee import Fee
from app.models.geo import GeoPoint
from app.models.pierre import FeePolicy
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion
from app.actors.schemas import ActorCreate, ActorOut, ActorStatusUpdate

router = APIRouter(prefix=f"{settings.api_prefix}/actors", tags=["actors"])
ALLOWED_FILIERES = {"OR", "PIERRE", "BOIS"}


@router.post("", response_model=ActorOut, status_code=201)
def create_actor(
    payload: ActorCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(get_optional_actor),
):
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
    if current_actor:
        if not _is_admin(db, current_actor.id) and not _is_commune_agent(db, current_actor.id):
            raise bad_request("acces_refuse")
        if _is_commune_agent(db, current_actor.id) and current_actor.commune_id != commune.id:
            raise bad_request("acces_refuse")

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
    raw_filieres = payload.filieres or []
    filieres = sorted({f.strip().upper() for f in raw_filieres if (f or "").strip()})
    if not filieres:
        filieres = ["OR"]
    if any(f not in ALLOWED_FILIERES for f in filieres):
        raise bad_request("filiere_invalide")

    for role in roles:
        db.add(ActorRole(actor_id=actor.id, role=role, status="active"))
    for filiere in filieres:
        db.add(ActorFiliere(actor_id=actor.id, filiere=filiere))

    opening_fee = None
    if any(r in {"orpailleur", "collecteur", "comptoir", "comptoir_operator"} for r in roles):
        opening_fee_amount = _resolve_opening_fee_amount(
            db=db,
            commune_id=commune.id,
            filiere=(filieres[0] if filieres else "OR"),
        )
        opening_fee = Fee(
            fee_type="account_opening_commune",
            actor_id=actor.id,
            commune_id=commune.id,
            amount=opening_fee_amount,
            currency="MGA",
            status="pending",
        )
        db.add(opening_fee)

    geo_point.actor_id = actor.id
    write_audit(
        db,
        actor_id=actor.id,
        action="actor_created",
        entity_type="actor",
        entity_id=str(actor.id),
        justification=None,
        meta={"roles": roles},
    )
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
        region_code=region.code,
        district_code=district.code,
        commune_code=commune.code,
        fokontany_code=fokontany.code if fokontany else None,
        opening_fee_id=opening_fee.id if opening_fee else None,
        opening_fee_status=opening_fee.status if opening_fee else None,
        filieres=filieres,
        laissez_passer_access_status=actor.laissez_passer_access_status,
        agrement_status=actor.agrement_status,
        sig_oc_access_status=actor.sig_oc_access_status,
    )


@router.get("/{actor_id}", response_model=ActorOut)
def get_actor(
    actor_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    if not _is_admin(db, current_actor.id) and current_actor.id != actor.id:
        raise bad_request("acces_refuse")
    region = db.query(Region).filter_by(id=actor.region_id).first()
    district = db.query(District).filter_by(id=actor.district_id).first()
    commune = db.query(Commune).filter_by(id=actor.commune_id).first()
    fokontany = (
        db.query(Fokontany).filter_by(id=actor.fokontany_id).first()
        if actor.fokontany_id
        else None
    )
    return ActorOut(
        id=actor.id,
        type_personne=actor.type_personne,
        nom=actor.nom,
        prenoms=actor.prenoms,
        telephone=actor.telephone,
        email=actor.email,
        status=actor.status,
        region_code=region.code if region else "",
        district_code=district.code if district else "",
        commune_code=commune.code if commune else "",
        fokontany_code=fokontany.code if fokontany else None,
        opening_fee_id=_get_opening_fee_id(db, actor.id),
        opening_fee_status=_get_opening_fee_status(db, actor.id),
        filieres=_get_actor_filieres(db, actor.id),
        laissez_passer_access_status=actor.laissez_passer_access_status,
        agrement_status=actor.agrement_status,
        sig_oc_access_status=actor.sig_oc_access_status,
    )


@router.get("/{actor_id}/roles")
def get_actor_roles(
    actor_id: int,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if not _is_admin(db, current_actor.id) and current_actor.id != actor_id:
        raise bad_request("acces_refuse")
    roles = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    return {"actor_id": actor_id, "roles": [r.role for r in roles]}


@router.patch("/{actor_id}/status", response_model=ActorOut)
def update_actor_status(
    actor_id: int,
    payload: ActorStatusUpdate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent"})),
):
    """Valider ou rejeter un acteur (statut pending → active ou rejected). Réservé maire/commune_agent (même commune) ou admin."""
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    if actor.status != "pending":
        raise bad_request("acteur_invalide")  # déjà traité
    is_admin_or_dir = _is_admin(db, current_actor.id)
    is_commune_agent = _is_commune_agent(db, current_actor.id)
    if is_commune_agent and current_actor.commune_id != actor.commune_id:
        raise bad_request("acces_refuse_commune")
    if not is_admin_or_dir and not is_commune_agent:
        raise bad_request("acces_refuse")
    if payload.status not in ("active", "rejected"):
        raise bad_request("acteur_invalide")
    if payload.status == "active" and _requires_commune_fee_validation(db, actor.id):
        if _get_opening_fee_status(db, actor.id) != "paid":
            raise bad_request("frais_ouverture_non_payes")
    actor.status = payload.status
    write_audit(
        db,
        actor_id=current_actor.id,
        action="actor_status_updated",
        entity_type="actor",
        entity_id=str(actor_id),
        justification=None,
        meta={"new_status": payload.status},
    )
    db.commit()
    db.refresh(actor)
    region = db.query(Region).filter_by(id=actor.region_id).first()
    district = db.query(District).filter_by(id=actor.district_id).first()
    commune = db.query(Commune).filter_by(id=actor.commune_id).first()
    fokontany = (
        db.query(Fokontany).filter_by(id=actor.fokontany_id).first()
        if actor.fokontany_id
        else None
    )
    return ActorOut(
        id=actor.id,
        type_personne=actor.type_personne,
        nom=actor.nom,
        prenoms=actor.prenoms,
        telephone=actor.telephone,
        email=actor.email,
        status=actor.status,
        region_code=region.code if region else "",
        district_code=district.code if district else "",
        commune_code=commune.code if commune else "",
        fokontany_code=fokontany.code if fokontany else None,
        opening_fee_id=_get_opening_fee_id(db, actor.id),
        opening_fee_status=_get_opening_fee_status(db, actor.id),
        filieres=_get_actor_filieres(db, actor.id),
        laissez_passer_access_status=actor.laissez_passer_access_status,
        agrement_status=actor.agrement_status,
        sig_oc_access_status=actor.sig_oc_access_status,
    )


@router.get("", response_model=list[ActorOut])
def list_actors(
    role: str | None = None,
    filiere: str | None = None,
    commune_code: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "commune_agent"})),
):
    query = db.query(Actor).filter(Actor.status != "blocked")

    is_commune_agent = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == current_actor.id, ActorRole.role == "commune_agent")
        .first()
        is not None
    )
    if is_commune_agent:
        query = query.filter(Actor.commune_id == current_actor.commune_id)

    if status:
        query = query.filter(Actor.status == status)
    if role:
        query = query.join(ActorRole).filter(ActorRole.role == role)
    if filiere:
        query = query.join(ActorFiliere, ActorFiliere.actor_id == Actor.id).filter(
            ActorFiliere.filiere == filiere.strip().upper()
        )

    if commune_code:
        commune = (
            db.query(Commune)
            .filter(Commune.code == commune_code)
            .first()
        )
        if not commune:
            return []
        query = query.filter(Actor.commune_id == commune.id)

    actors = query.distinct().order_by(Actor.created_at.desc()).all()
    results = []
    for actor in actors:
        region = db.query(Region).filter_by(id=actor.region_id).first()
        district = db.query(District).filter_by(id=actor.district_id).first()
        commune = db.query(Commune).filter_by(id=actor.commune_id).first()
        fokontany = (
            db.query(Fokontany).filter_by(id=actor.fokontany_id).first()
            if actor.fokontany_id
            else None
        )
        results.append(
            ActorOut(
                id=actor.id,
                type_personne=actor.type_personne,
                nom=actor.nom,
                prenoms=actor.prenoms,
                telephone=actor.telephone,
                email=actor.email,
                status=actor.status,
                region_code=region.code if region else "",
                district_code=district.code if district else "",
                commune_code=commune.code if commune else "",
                fokontany_code=fokontany.code if fokontany else None,
                opening_fee_id=_get_opening_fee_id(db, actor.id),
                opening_fee_status=_get_opening_fee_status(db, actor.id),
                filieres=_get_actor_filieres(db, actor.id),
                laissez_passer_access_status=actor.laissez_passer_access_status,
                agrement_status=actor.agrement_status,
                sig_oc_access_status=actor.sig_oc_access_status,
            )
        )
    return results


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


def _get_opening_fee_id(db: Session, actor_id: int) -> int | None:
    fee = (
        db.query(Fee)
        .filter(Fee.actor_id == actor_id, Fee.fee_type == "account_opening_commune")
        .order_by(Fee.id.desc())
        .first()
    )
    return fee.id if fee else None


def _get_opening_fee_status(db: Session, actor_id: int) -> str | None:
    fee = (
        db.query(Fee)
        .filter(Fee.actor_id == actor_id, Fee.fee_type == "account_opening_commune")
        .order_by(Fee.id.desc())
        .first()
    )
    return fee.status if fee else None


def _get_actor_filieres(db: Session, actor_id: int) -> list[str]:
    rows = (
        db.query(ActorFiliere.filiere)
        .filter(ActorFiliere.actor_id == actor_id)
        .order_by(ActorFiliere.filiere.asc())
        .all()
    )
    return [row[0] for row in rows]


def _requires_commune_fee_validation(db: Session, actor_id: int) -> bool:
    roles = (
        db.query(ActorRole.role)
        .filter(ActorRole.actor_id == actor_id, ActorRole.status == "active")
        .all()
    )
    role_codes = {r[0] for r in roles}
    return any(role in {"orpailleur", "collecteur", "comptoir", "comptoir_operator"} for role in role_codes)


def _resolve_opening_fee_amount(db: Session, commune_id: int, filiere: str) -> int:
    now = datetime.now(timezone.utc)
    policy = (
        db.query(FeePolicy)
        .filter(FeePolicy.fee_type == "account_opening_commune")
        .filter(FeePolicy.filiere == (filiere or "OR").upper())
        .filter(FeePolicy.status == "active")
        .filter(FeePolicy.effective_from <= now)
        .filter((FeePolicy.effective_to == None) | (FeePolicy.effective_to >= now))
        .filter((FeePolicy.commune_id == commune_id) | (FeePolicy.commune_id == None))
        .order_by(FeePolicy.commune_id.desc(), FeePolicy.effective_from.desc())
        .first()
    )
    if policy:
        return int(policy.amount)
    return 10000
