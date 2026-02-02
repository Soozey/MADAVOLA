from fastapi import FastAPI

from app.actors.router import router as actors_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.documents.router import router as documents_router
from app.fees.router import router as fees_router
from app.geopoints.router import router as geopoints_router
from app.health.router import router as health_router
from app.invoices.router import router as invoices_router
from app.ledger.router import router as ledger_router
from app.lots.router import router as lots_router
from app.payments.router import router as payments_router
from app.payments.providers_router import router as payment_providers_router
from app.territories.router import router as territories_router
from app.transactions.router import router as transactions_router


def create_app() -> FastAPI:
    app = FastAPI(title="MADAVOLA API", version="v1")
    app.include_router(auth_router)
    app.include_router(audit_router)
    app.include_router(documents_router)
    app.include_router(actors_router)
    app.include_router(fees_router)
    app.include_router(geopoints_router)
    app.include_router(health_router)
    app.include_router(invoices_router)
    app.include_router(ledger_router)
    app.include_router(lots_router)
    app.include_router(payments_router)
    app.include_router(payment_providers_router)
    app.include_router(territories_router)
    app.include_router(transactions_router)
    return app


app = create_app()
