from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Forcer UTF-8 pour éviter les problèmes d'accents (PostgreSQL)
_connect_args = {}
if "postgresql" in settings.database_url:
    _connect_args["options"] = "-c client_encoding=UTF8"

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
