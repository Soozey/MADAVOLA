from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.actors.router import router as actors_router
from app.admin.router import router as admin_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.dashboards.router import router as dashboards_router
from app.documents.router import router as documents_router
from app.exports.router import router as exports_router
from app.fees.router import router as fees_router
from app.geopoints.router import router as geopoints_router
from app.health.router import router as health_router
from app.invoices.router import router as invoices_router
from app.inspections.router import router as inspections_router
from app.ledger.router import router as ledger_router
from app.lots.router import router as lots_router
from app.payments.router import router as payments_router
from app.payments.providers_router import router as payment_providers_router
from app.penalties.router import router as penalties_router
from app.reports.router import router as reports_router
from app.roles.router import router as roles_router
from app.territories.router import router as territories_router
from app.transactions.router import router as transactions_router
from app.verify.router import router as verify_router
from app.violations.router import router as violations_router


def create_app() -> FastAPI:
    app = FastAPI(title="MADAVOLA API", version="v1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(audit_router)
    app.include_router(dashboards_router)
    app.include_router(documents_router)
    app.include_router(actors_router)
    app.include_router(fees_router)
    app.include_router(geopoints_router)
    app.include_router(health_router)
    app.include_router(invoices_router)
    app.include_router(inspections_router)
    app.include_router(ledger_router)
    app.include_router(lots_router)
    app.include_router(payments_router)
    app.include_router(payment_providers_router)
    app.include_router(penalties_router)
    app.include_router(reports_router)
    app.include_router(roles_router)
    app.include_router(territories_router)
    app.include_router(transactions_router)
    app.include_router(verify_router)
    app.include_router(violations_router)
    app.include_router(exports_router)
    return app


app = create_app()
