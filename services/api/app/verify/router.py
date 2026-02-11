"""
Endpoints publics de vérification (sans auth) pour le scan QR par les contrôleurs.
Le QR sur la carte orpailleur/collecteur pointe vers la page front /verify/actor/:id
qui appelle GET /api/v1/verify/actor/:id pour afficher l'identité.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.actor import Actor
from app.models.territory import Commune
from app.verify.schemas import ActorVerifyOut

router = APIRouter(prefix=f"{settings.api_prefix}/verify", tags=["verify"])


@router.get("/actor/{actor_id}", response_model=ActorVerifyOut)
def verify_actor(actor_id: int, db: Session = Depends(get_db)):
    """
    Vérification publique d'un acteur (scan QR par contrôleur).
    Retourne les infos minimales : id, nom, prénoms, statut, commune.
    Pas d'authentification requise pour permettre le scan sur le terrain.
    """
    actor = db.query(Actor).filter_by(id=actor_id).first()
    if not actor:
        raise bad_request("acteur_introuvable")
    commune = db.query(Commune).filter_by(id=actor.commune_id).first() if actor.commune_id else None
    return ActorVerifyOut(
        id=actor.id,
        nom=actor.nom,
        prenoms=actor.prenoms,
        statut=actor.status,
        commune_code=commune.code if commune else "",
        type_personne=actor.type_personne,
    )
