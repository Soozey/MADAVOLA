from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.payment import PaymentProvider
from app.payments.schemas import PaymentProviderCreate, PaymentProviderOut, PaymentProviderUpdate

router = APIRouter(prefix=f"{settings.api_prefix}/payment-providers", tags=["payments"])


@router.post("", response_model=PaymentProviderOut, status_code=201)
def create_provider(
    payload: PaymentProviderCreate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    exists = db.query(PaymentProvider).filter_by(code=payload.code).first()
    if exists:
        raise bad_request("provider_existe_deja")
    provider = PaymentProvider(
        code=payload.code,
        name=payload.name,
        enabled=payload.enabled,
        config_json=payload.config_json,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return PaymentProviderOut(
        id=provider.id,
        code=provider.code,
        name=provider.name,
        enabled=provider.enabled,
        config_json=provider.config_json,
    )


@router.get("", response_model=list[PaymentProviderOut])
def list_providers(
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    providers = db.query(PaymentProvider).order_by(PaymentProvider.code.asc()).all()
    return [
        PaymentProviderOut(
            id=p.id,
            code=p.code,
            name=p.name,
            enabled=p.enabled,
            config_json=p.config_json,
        )
        for p in providers
    ]


@router.patch("/{provider_id}", response_model=PaymentProviderOut)
def update_provider(
    provider_id: int,
    payload: PaymentProviderUpdate,
    db: Session = Depends(get_db),
    _actor=Depends(require_roles({"admin"})),
):
    provider = db.query(PaymentProvider).filter_by(id=provider_id).first()
    if not provider:
        raise bad_request("provider_introuvable")
    if payload.name is not None:
        provider.name = payload.name
    if payload.enabled is not None:
        provider.enabled = payload.enabled
    if payload.config_json is not None:
        provider.config_json = payload.config_json
    db.commit()
    db.refresh(provider)
    return PaymentProviderOut(
        id=provider.id,
        code=provider.code,
        name=provider.name,
        enabled=provider.enabled,
        config_json=provider.config_json,
    )
