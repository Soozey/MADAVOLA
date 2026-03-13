import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.bois import EssenceCatalog
from pydantic import BaseModel


class EssenceIn(BaseModel):
    code_essence: str
    nom: str
    categorie: str
    export_autorise: bool = True
    requires_cites: bool = False
    rules_json: dict = {}
    status: str = "active"


class EssenceUpdate(BaseModel):
    nom: str | None = None
    categorie: str | None = None
    export_autorise: bool | None = None
    requires_cites: bool | None = None
    rules_json: dict | None = None
    status: str | None = None


class EssenceOut(BaseModel):
    id: int
    code_essence: str
    nom: str
    categorie: str
    export_autorise: bool
    requires_cites: bool
    rules_json: dict
    status: str


router = APIRouter(prefix=f"{settings.api_prefix}/catalog/essences", tags=["wood_catalog"])


@router.get("", response_model=list[EssenceOut])
def list_essences(
    categorie: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(EssenceCatalog).filter(EssenceCatalog.status != "deleted")
    if categorie:
        query = query.filter(EssenceCatalog.categorie == categorie)
    rows = query.order_by(EssenceCatalog.code_essence.asc()).all()
    return [
        EssenceOut(
            id=r.id,
            code_essence=r.code_essence,
            nom=r.nom,
            categorie=r.categorie,
            export_autorise=bool(r.export_autorise),
            requires_cites=bool(r.requires_cites),
            rules_json=json.loads(r.rules_json or "{}"),
            status=r.status,
        )
        for r in rows
    ]


@router.post("", response_model=EssenceOut, status_code=201)
def create_essence(
    payload: EssenceIn,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "forets", "bois_admin_central"})),
):
    if payload.categorie not in {"A_protegee", "B_artisanale", "C_autre"}:
        raise bad_request("categorie_invalide")
    code = payload.code_essence.strip().upper()
    if db.query(EssenceCatalog.id).filter(EssenceCatalog.code_essence == code).first():
        raise bad_request("essence_code_existant")
    row = EssenceCatalog(
        code_essence=code,
        nom=payload.nom.strip(),
        categorie=payload.categorie,
        export_autorise=1 if payload.export_autorise else 0,
        requires_cites=1 if payload.requires_cites else 0,
        rules_json=json.dumps(payload.rules_json or {}, ensure_ascii=True),
        status=payload.status,
        created_by_actor_id=current_actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return EssenceOut(
        id=row.id,
        code_essence=row.code_essence,
        nom=row.nom,
        categorie=row.categorie,
        export_autorise=bool(row.export_autorise),
        requires_cites=bool(row.requires_cites),
        rules_json=json.loads(row.rules_json or "{}"),
        status=row.status,
    )


@router.put("/{essence_id}", response_model=EssenceOut)
def update_essence(
    essence_id: int,
    payload: EssenceUpdate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "forets", "bois_admin_central"})),
):
    row = db.query(EssenceCatalog).filter_by(id=essence_id).first()
    if not row:
        raise bad_request("essence_introuvable")
    if payload.nom is not None:
        row.nom = payload.nom.strip()
    if payload.categorie is not None:
        if payload.categorie not in {"A_protegee", "B_artisanale", "C_autre"}:
            raise bad_request("categorie_invalide")
        row.categorie = payload.categorie
    if payload.export_autorise is not None:
        row.export_autorise = 1 if payload.export_autorise else 0
    if payload.requires_cites is not None:
        row.requires_cites = 1 if payload.requires_cites else 0
    if payload.rules_json is not None:
        row.rules_json = json.dumps(payload.rules_json, ensure_ascii=True)
    if payload.status is not None:
        row.status = payload.status
    db.commit()
    db.refresh(row)
    return EssenceOut(
        id=row.id,
        code_essence=row.code_essence,
        nom=row.nom,
        categorie=row.categorie,
        export_autorise=bool(row.export_autorise),
        requires_cites=bool(row.requires_cites),
        rules_json=json.loads(row.rules_json or "{}"),
        status=row.status,
    )


@router.delete("/{essence_id}")
def delete_essence(
    essence_id: int,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "forets", "bois_admin_central"})),
):
    row = db.query(EssenceCatalog).filter_by(id=essence_id).first()
    if not row:
        raise bad_request("essence_introuvable")
    row.status = "deleted"
    db.commit()
    return {"status": "ok"}
