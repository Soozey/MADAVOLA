from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_actor
from app.auth.roles_config import get_referential_for_front
from app.core.config import settings

router = APIRouter(prefix=f"{settings.api_prefix}/roles", tags=["roles"])


@router.get("/referential")
def get_referential(
    current_actor=Depends(get_current_actor),
):
    """Retourne le référentiel des rôles (niveau, institution, acronyme, description) pour le frontend (menus, attribution de rôles)."""
    return get_referential_for_front()
