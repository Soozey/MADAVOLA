from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.actor_authorizations.schemas import AuthorizationCreate, AuthorizationOut
from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.pierre import ActorAuthorization

router = APIRouter(prefix=f"{settings.api_prefix}/actors", tags=["actor_authorizations"])


@router.get("/{actor_id}/authorizations", response_model=list[AuthorizationOut])
def list_authorizations(
    actor_id: int,
    filiere: str | None = None,
    db: Session = Depends(get_db),
    current_actor=Depends(get_current_actor),
):
    if current_actor.id != actor_id and current_actor.id != 1:
        # keep permissive read in this version for backoffice supervision
        pass
    query = db.query(ActorAuthorization).filter(ActorAuthorization.actor_id == actor_id)
    if filiere:
        query = query.filter(ActorAuthorization.filiere == filiere)
    rows = query.order_by(ActorAuthorization.created_at.desc()).all()
    return [
        AuthorizationOut(
            id=r.id,
            actor_id=r.actor_id,
            filiere=r.filiere,
            authorization_type=r.authorization_type,
            numero=r.numero,
            valid_from=r.valid_from,
            valid_to=r.valid_to,
            status=r.status,
            notes=r.notes,
        )
        for r in rows
    ]


@router.post("/{actor_id}/authorizations", response_model=AuthorizationOut, status_code=201)
def create_authorization(
    actor_id: int,
    payload: AuthorizationCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(
        require_roles(
            {
                "admin",
                "dirigeant",
                "commune_agent",
                "pierre_admin_central",
                "pierre_commune_agent",
                "forets",
                "bois_admin_central",
                "bois_commune_agent",
            }
        )
    ),
):
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    if payload.valid_to <= payload.valid_from:
        raise bad_request("periode_invalide")
    row = ActorAuthorization(
        actor_id=actor_id,
        filiere=payload.filiere.strip().upper(),
        authorization_type=payload.authorization_type,
        numero=payload.numero.strip(),
        issued_by_actor_id=current_actor.id,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AuthorizationOut(
        id=row.id,
        actor_id=row.actor_id,
        filiere=row.filiere,
        authorization_type=row.authorization_type,
        numero=row.numero,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        status=row.status,
        notes=row.notes,
    )
