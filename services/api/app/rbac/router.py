from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import Session
import logging

from app.auth.dependencies import get_current_actor
from app.auth.roles_config import ROLE_DEFINITIONS, get_permissions_for_role, roles_with_permission
from app.core.config import settings
from app.db import get_db
from app.models.actor import ActorRole
from app.models.rbac import RoleCatalog

router = APIRouter(prefix=f"{settings.api_prefix}/rbac", tags=["rbac"])
logger = logging.getLogger(__name__)

COMMON_SCOPED_ROLES = {
    "admin",
    "dirigeant",
    "acteur",
    "commune_agent",
    "police",
    "controleur",
    "transporteur",
    "transporteur_agree",
    "region_agent",
    "district_agent",
    "region",
    "commune",
}

OR_SCOPED_ROLES = {
    "orpailleur",
    "collecteur",
    "comptoir_operator",
    "comptoir_compliance",
    "comptoir_director",
    "com",
    "com_admin",
    "com_agent",
    "gue",
    "gue_or_agent",
    "douanes_agent",
    "raffinerie_agent",
    "lab_bgglm",
    "mines_region_agent",
    "bijoutier",
}


class RoleOut(BaseModel):
    code: str
    label: str
    description: str
    category: str
    actor_type: str
    filiere_scope: list[str]
    tags: list[str]
    is_active: bool
    display_order: int


class PermissionsOut(BaseModel):
    role: str
    permissions: list[str]


def _infer_filiere_scope(role_code: str) -> list[str]:
    if role_code.startswith("pierre_"):
        return ["PIERRE"]
    if role_code.startswith("bois_"):
        return ["BOIS"]
    if role_code in OR_SCOPED_ROLES:
        return ["OR"]
    if role_code in COMMON_SCOPED_ROLES:
        return ["OR", "PIERRE", "BOIS"]
    return ["OR", "PIERRE", "BOIS"]


def _label(code: str) -> str:
    return code.replace("_", " ").strip().title()


def _category(code: str) -> str:
    if code.startswith("bois_"):
        return "BOIS"
    if code.startswith("pierre_"):
        return "PIERRE"
    if code in {"orpailleur", "collecteur", "bijoutier", "acteur", "transporteur", "transporteur_agree"}:
        return "Acteurs terrain"
    if code in {"police", "gendarmerie", "controleur", "douanes_agent", "dgd", "mines_region_agent", "bois_controleur", "pierre_controleur_mines", "pierre_douanes"}:
        return "Controle"
    if code in {"commune", "commune_agent", "fokontany", "region", "region_agent", "district_agent", "bois_commune_agent", "pierre_commune_agent"}:
        return "Territorial"
    if code in {"com", "com_admin", "com_agent", "gue", "gue_or_agent", "comptoir_operator", "comptoir_compliance", "comptoir_director", "bois_exportateur", "pierre_exportateur"}:
        return "Export et regulation"
    return "Administration"


def _actor_type(code: str) -> str:
    if code in {
        "orpailleur",
        "collecteur",
        "bijoutier",
        "acteur",
        "transporteur",
        "transporteur_agree",
        "bois_exploitant",
        "bois_collecteur",
        "bois_transporteur",
        "bois_scieur",
        "bois_artisan",
        "bois_negociant",
        "bois_exportateur",
        "pierre_exploitant",
        "pierre_collecteur",
        "pierre_lapidaire",
        "pierre_negociant",
        "pierre_exportateur",
    }:
        return "USAGER"
    if code in {
        "commune",
        "commune_agent",
        "region",
        "region_agent",
        "district_agent",
        "fokontany",
        "police",
        "gendarmerie",
        "controleur",
        "douanes_agent",
        "gue_or_agent",
        "mines_region_agent",
        "lab_bgglm",
        "bois_commune_agent",
        "bois_agent_region",
        "bois_eaux_forets",
        "bois_douanes",
        "bois_controleur",
        "pierre_commune_agent",
        "pierre_controleur_mines",
        "pierre_douanes",
    }:
        return "AGENT_ETAT"
    if code in {
        "com",
        "com_admin",
        "com_agent",
        "comptoir_operator",
        "comptoir_director",
        "comptoir_compliance",
        "raffinerie_agent",
        "admin",
        "dirigeant",
    }:
        return "OPERATEUR_PRIVE"
    return "TRANSVERSAL"


def _scope_from_csv(raw: str | None) -> list[str]:
    if not raw:
        return ["OR", "PIERRE", "BOIS"]
    out = [x.strip().upper() for x in raw.split(",") if x.strip()]
    return out or ["OR", "PIERRE", "BOIS"]


def _tags_from_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


class FiliereOut(BaseModel):
    code: str
    label: str


@router.get("/filieres", response_model=list[FiliereOut])
def list_filieres(_actor=Depends(get_current_actor)):
    return [
        FiliereOut(code="OR", label="OR"),
        FiliereOut(code="PIERRE", label="PIERRE"),
        FiliereOut(code="BOIS", label="BOIS"),
    ]


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    filiere: str | None = None,
    include_common: bool = True,
    search: str | None = None,
    category: str | None = None,
    actor_type: str | None = None,
    active_only: bool = True,
    for_current_actor: bool = False,
    include_admin_catalog: bool = False,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    target = (filiere or "").strip().upper() or None
    raw_search = (search or "").strip().lower()
    target_category = (category or "").strip().lower()
    target_actor_type = (actor_type or "").strip().upper()

    catalog_rows: dict[str, RoleCatalog] = {}
    if inspect(db.bind).has_table(RoleCatalog.__tablename__):
        for item in db.query(RoleCatalog).all():
            catalog_rows[item.code] = item

    allowed_codes: set[str] | None = None
    if for_current_actor:
        actor_roles = (
            db.query(ActorRole.role)
            .filter(
                ActorRole.actor_id == _actor.id,
                ActorRole.status == "active",
            )
            .all()
        )
        actor_codes = {r[0] for r in actor_roles}
        is_admin_like = bool(actor_codes.intersection({"admin", "dirigeant"}))
        if is_admin_like and include_admin_catalog:
            allowed_codes = None
        else:
            allowed_codes = actor_codes

    role_codes: list[str] = sorted(ROLE_DEFINITIONS.keys())
    if allowed_codes is not None:
        # Safety net: keep actor roles visible even if a legacy role code is missing from ROLE_DEFINITIONS.
        role_codes = sorted(set(role_codes).union(allowed_codes))

    rows: list[RoleOut] = []
    for idx, code in enumerate(role_codes, start=1):
        if allowed_codes is not None and code not in allowed_codes:
            continue
        defn = ROLE_DEFINITIONS.get(
            code,
            {
                "description": "Role legacy detecte sur le compte; catalogue RBAC a harmoniser.",
                "permissions": [],
            },
        )

        catalog = catalog_rows.get(code)
        scope = _scope_from_csv(catalog.filiere_scope_csv) if catalog else _infer_filiere_scope(code)
        if target and target not in scope:
            if not (include_common and set(scope) == {"OR", "PIERRE", "BOIS"}):
                continue
        if target and not include_common and set(scope) == {"OR", "PIERRE", "BOIS"}:
            continue

        row_category = (catalog.category if catalog else _category(code)).strip()
        row_label = (catalog.label if catalog else _label(code)).strip()
        row_description = (catalog.description if catalog else defn.get("description", "")).strip()
        row_actor_type = _actor_type(code)
        row_active = bool(catalog.is_active) if catalog else True
        row_order = int(catalog.display_order) if catalog else idx
        row_tags = _tags_from_csv(catalog.tags_csv) if catalog else []

        if active_only and not row_active:
            continue
        if target_category and row_category.lower() != target_category:
            continue
        if target_actor_type and row_actor_type != target_actor_type:
            continue
        if raw_search:
            hay = " ".join([code, row_label, row_description, row_category, " ".join(row_tags)]).lower()
            if raw_search not in hay:
                continue

        rows.append(
            RoleOut(
                code=code,
                label=row_label,
                description=row_description,
                category=row_category,
                actor_type=row_actor_type,
                filiere_scope=scope,
                tags=row_tags,
                is_active=row_active,
                display_order=row_order,
            )
        )

    rows.sort(key=lambda r: (r.display_order, r.category.lower(), r.label.lower(), r.code.lower()))
    logger.debug(
        "rbac.roles",
        extra={
            "actor_id": _actor.id,
            "filiere": target,
            "search": raw_search,
            "category": target_category,
            "actor_type": target_actor_type,
            "for_current_actor": for_current_actor,
            "count": len(rows),
        },
    )
    return rows


@router.get("/permissions", response_model=PermissionsOut)
def get_permissions(
    role: str,
    _actor=Depends(get_current_actor),
):
    logger.debug("rbac.permissions", extra={"actor_id": _actor.id, "role": role})
    return PermissionsOut(role=role, permissions=get_permissions_for_role(role))


@router.get("/roles-with-permission")
def get_roles_with_permission(
    permission: str,
    _actor=Depends(get_current_actor),
):
    return {"permission": permission, "roles": sorted(roles_with_permission(permission))}
