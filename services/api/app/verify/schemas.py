from pydantic import BaseModel


class ActorVerifyOut(BaseModel):
    """Informations minimales pour vérification par scan QR (carte orpailleur/collecteur)."""
    id: int
    nom: str
    prenoms: str | None
    statut: str
    commune_code: str
    type_personne: str
