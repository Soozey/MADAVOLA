from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db

router = APIRouter(prefix=f"{settings.api_prefix}", tags=["admin"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "db_indisponible"},
        ) from exc
    return {"status": "ready"}
