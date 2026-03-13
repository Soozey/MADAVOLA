import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_actor, require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.pierre import ProductCatalog
from app.catalog.schemas import ProductCatalogCreate, ProductCatalogOut, ProductCatalogUpdate

router = APIRouter(prefix=f"{settings.api_prefix}/catalog/products", tags=["catalog"])


def _to_out(row: ProductCatalog) -> ProductCatalogOut:
    return ProductCatalogOut(
        id=row.id,
        code=row.code,
        nom=row.nom,
        famille=row.famille,
        filiere=row.filiere,
        sous_filiere=row.sous_filiere,
        allowed_units=json.loads(row.allowed_units_json or "[]"),
        required_attributes=json.loads(row.required_attributes_json or "[]"),
        export_restricted=bool(row.export_restricted),
        export_rules=json.loads(row.export_rules_json or "{}"),
        status=row.status,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ProductCatalogOut])
def list_products(
    filiere: str | None = None,
    sous_filiere: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(get_current_actor),
):
    query = db.query(ProductCatalog).filter(ProductCatalog.status != "deleted")
    if filiere:
        query = query.filter(ProductCatalog.filiere == filiere)
    if sous_filiere:
        query = query.filter(ProductCatalog.sous_filiere == sous_filiere)
    return [_to_out(r) for r in query.order_by(ProductCatalog.code.asc()).all()]


@router.post("", response_model=ProductCatalogOut, status_code=201)
def create_product(
    payload: ProductCatalogCreate,
    db: Session = Depends(get_db),
    current_actor=Depends(require_roles({"admin", "dirigeant", "pierre_admin_central", "com_admin"})),
):
    if db.query(ProductCatalog).filter(ProductCatalog.code == payload.code).first():
        raise bad_request("catalog_code_existant")
    row = ProductCatalog(
        code=payload.code.strip().upper(),
        nom=payload.nom.strip(),
        famille=payload.famille,
        filiere=payload.filiere.strip().upper(),
        sous_filiere=payload.sous_filiere.strip().upper(),
        allowed_units_json=json.dumps(payload.allowed_units, ensure_ascii=True),
        required_attributes_json=json.dumps(payload.required_attributes, ensure_ascii=True),
        export_restricted=1 if payload.export_restricted else 0,
        export_rules_json=json.dumps(payload.export_rules, ensure_ascii=True),
        status="active",
        created_by_actor_id=current_actor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.put("/{product_id}", response_model=ProductCatalogOut)
def update_product(
    product_id: int,
    payload: ProductCatalogUpdate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "pierre_admin_central", "com_admin"})),
):
    row = db.query(ProductCatalog).filter_by(id=product_id).first()
    if not row:
        raise bad_request("catalog_introuvable")
    if payload.nom is not None:
        row.nom = payload.nom.strip()
    if payload.sous_filiere is not None:
        row.sous_filiere = payload.sous_filiere.strip().upper()
    if payload.allowed_units is not None:
        row.allowed_units_json = json.dumps(payload.allowed_units, ensure_ascii=True)
    if payload.required_attributes is not None:
        row.required_attributes_json = json.dumps(payload.required_attributes, ensure_ascii=True)
    if payload.export_restricted is not None:
        row.export_restricted = 1 if payload.export_restricted else 0
    if payload.export_rules is not None:
        row.export_rules_json = json.dumps(payload.export_rules, ensure_ascii=True)
    if payload.status is not None:
        row.status = payload.status
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin", "dirigeant", "pierre_admin_central", "com_admin"})),
):
    row = db.query(ProductCatalog).filter_by(id=product_id).first()
    if not row:
        raise bad_request("catalog_introuvable")
    row.status = "deleted"
    db.commit()
    return {"status": "ok"}
