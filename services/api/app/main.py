from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.core.config import settings
from sqlalchemy import text
from app.actors.router import router as actors_router
from app.admin.router import router as admin_router
from app.audit.router import router as audit_router
from app.approvals.router import router as approvals_router
from app.catalog.router import router as catalog_router
from app.actor_authorizations.router import router as actor_authorizations_router
from app.auth.router import router as auth_router
from app.dashboards.router import router as dashboards_router
from app.documents.router import router as documents_router
from app.emergency_alerts.router import router as emergency_alerts_router
from app.exports.router import router as exports_router
from app.fees.router import router as fees_router
from app.geopoints.router import router as geopoints_router
from app.health.router import router as health_router
from app.invoices.router import router as invoices_router
from app.inspections.router import router as inspections_router
from app.karabola.router import router as karabola_router
from app.ledger.router import router as ledger_router
from app.lots.router import router as lots_router
from app.marketplace.router import router as marketplace_router
from app.messages.router import router as messages_router
from app.payments.router import router as payments_router
from app.payments.providers_router import router as payment_providers_router
from app.notifications.router import router as notifications_router
from app.penalties.router import router as penalties_router
from app.reports.router import router as reports_router
from app.rbac.router import router as rbac_router
from app.regime_or.router import router as regime_or_router
from app.or_compliance.router import router as or_compliance_router
from app.roles.router import router as roles_router
from app.territories.router import router as territories_router
from app.taxes.router import router as taxes_router
from app.transactions.router import router as transactions_router
from app.trades.router import router as trades_router
from app.transformations.router import router as transformations_router
from app.transports.router import router as transports_router
from app.verify.router import router as verify_router
from app.violations.router import router as violations_router
from app.wood_catalog.router import router as wood_catalog_router
from app.models.actor_filiere import ActorFiliere
from app.models.actor import ActorKYC, ActorWallet, CommuneProfile
from app.models.or_compliance import (
    CollectorAffiliationAgreement,
    CollectorCard,
    CollectorCardDocument,
    CollectorCardFeeSplit,
    CollectorRegister,
    CollectorSemiAnnualReport,
    ComplianceNotification,
    ComptoirLicense,
    KaraBolamenaCard,
    KaraProductionLog,
    OrTariffConfig,
)
from app.models.pierre import (
    ActorAuthorization,
    ExportColis,
    ExportSeal,
    ExportValidationStep,
    FeePolicy,
    PierreTransformationEvent,
    PierreTransformationLink,
    ProductCatalog,
)
from app.models.bois import (
    ChecklistPolicy,
    EssenceCatalog,
    RulePolicy,
    TransportRecord,
    TransportRecordItem,
    WorkflowApproval,
)
from app.models.rbac import RoleCatalog
from app.models.emergency import EmergencyAlert
from app.models.communication import ContactRequest, DirectMessage
from app.models.marketplace import MarketplaceOffer
from app.models.base import Base
from app.auth.roles_config import ROLE_DEFINITIONS


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
    app.include_router(approvals_router)
    app.include_router(catalog_router)
    app.include_router(actor_authorizations_router)
    app.include_router(dashboards_router)
    app.include_router(documents_router)
    app.include_router(emergency_alerts_router)
    app.include_router(actors_router)
    app.include_router(fees_router)
    app.include_router(geopoints_router)
    app.include_router(health_router)
    app.include_router(invoices_router)
    app.include_router(inspections_router)
    app.include_router(karabola_router)
    app.include_router(ledger_router)
    app.include_router(lots_router)
    app.include_router(marketplace_router)
    app.include_router(messages_router)
    app.include_router(payments_router)
    app.include_router(payment_providers_router)
    app.include_router(notifications_router)
    app.include_router(penalties_router)
    app.include_router(reports_router)
    app.include_router(rbac_router)
    app.include_router(regime_or_router)
    app.include_router(or_compliance_router)
    app.include_router(roles_router)
    app.include_router(territories_router)
    app.include_router(taxes_router)
    app.include_router(transactions_router)
    app.include_router(trades_router)
    app.include_router(transformations_router)
    app.include_router(transports_router)
    app.include_router(verify_router)
    app.include_router(violations_router)
    app.include_router(wood_catalog_router)
    app.include_router(exports_router)

    @app.get("/", tags=["system"])
    def root():
        return {
            "service": "MADAVOLA API",
            "version": "v1",
            "message": "API operationnelle",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "api_prefix": settings.api_prefix,
            "health": f"{settings.api_prefix}/health",
            "ready": f"{settings.api_prefix}/ready",
        }

    @app.on_event("startup")
    def ensure_optional_tables() -> None:
        if settings.database_url.startswith("sqlite"):
            Base.metadata.create_all(bind=engine, checkfirst=True)
        RoleCatalog.__table__.create(bind=engine, checkfirst=True)
        ActorKYC.__table__.create(bind=engine, checkfirst=True)
        ActorWallet.__table__.create(bind=engine, checkfirst=True)
        CommuneProfile.__table__.create(bind=engine, checkfirst=True)
        ActorFiliere.__table__.create(bind=engine, checkfirst=True)
        OrTariffConfig.__table__.create(bind=engine, checkfirst=True)
        KaraBolamenaCard.__table__.create(bind=engine, checkfirst=True)
        KaraProductionLog.__table__.create(bind=engine, checkfirst=True)
        CollectorCard.__table__.create(bind=engine, checkfirst=True)
        CollectorCardDocument.__table__.create(bind=engine, checkfirst=True)
        CollectorAffiliationAgreement.__table__.create(bind=engine, checkfirst=True)
        CollectorRegister.__table__.create(bind=engine, checkfirst=True)
        CollectorSemiAnnualReport.__table__.create(bind=engine, checkfirst=True)
        ComptoirLicense.__table__.create(bind=engine, checkfirst=True)
        CollectorCardFeeSplit.__table__.create(bind=engine, checkfirst=True)
        ComplianceNotification.__table__.create(bind=engine, checkfirst=True)
        ProductCatalog.__table__.create(bind=engine, checkfirst=True)
        ActorAuthorization.__table__.create(bind=engine, checkfirst=True)
        FeePolicy.__table__.create(bind=engine, checkfirst=True)
        ExportColis.__table__.create(bind=engine, checkfirst=True)
        ExportSeal.__table__.create(bind=engine, checkfirst=True)
        ExportValidationStep.__table__.create(bind=engine, checkfirst=True)
        PierreTransformationEvent.__table__.create(bind=engine, checkfirst=True)
        PierreTransformationLink.__table__.create(bind=engine, checkfirst=True)
        EssenceCatalog.__table__.create(bind=engine, checkfirst=True)
        RulePolicy.__table__.create(bind=engine, checkfirst=True)
        ChecklistPolicy.__table__.create(bind=engine, checkfirst=True)
        TransportRecord.__table__.create(bind=engine, checkfirst=True)
        TransportRecordItem.__table__.create(bind=engine, checkfirst=True)
        WorkflowApproval.__table__.create(bind=engine, checkfirst=True)
        EmergencyAlert.__table__.create(bind=engine, checkfirst=True)
        ContactRequest.__table__.create(bind=engine, checkfirst=True)
        DirectMessage.__table__.create(bind=engine, checkfirst=True)
        MarketplaceOffer.__table__.create(bind=engine, checkfirst=True)
        with engine.begin() as conn:
            existing_roles = conn.execute(text("SELECT COUNT(*) FROM rbac_role_catalog")).scalar() or 0
            if existing_roles == 0:
                rows = []
                for idx, (code, defn) in enumerate(sorted(ROLE_DEFINITIONS.items()), start=1):
                    if code.startswith("pierre_"):
                        scope = "PIERRE"
                        category = "PIERRE"
                    elif code.startswith("bois_"):
                        scope = "BOIS"
                        category = "BOIS"
                    elif code in {"orpailleur", "collecteur", "comptoir_operator", "comptoir_compliance", "comptoir_director", "com", "com_admin", "com_agent", "gue", "gue_or_agent", "douanes_agent", "raffinerie_agent", "lab_bgglm", "mines_region_agent", "bijoutier"}:
                        scope = "OR"
                        category = "OR"
                    else:
                        scope = "OR,PIERRE,BOIS"
                        category = "Administration"
                    rows.append(
                        {
                            "code": code,
                            "label": " ".join(x.capitalize() for x in code.split("_") if x),
                            "description": defn.get("description", ""),
                            "category": category,
                            "filiere_scope_csv": scope,
                            "display_order": idx,
                        }
                    )
                for row in rows:
                    conn.execute(
                        text(
                            "INSERT INTO rbac_role_catalog (code,label,description,category,filiere_scope_csv,display_order,is_active) "
                            "VALUES (:code,:label,:description,:category,:filiere_scope_csv,:display_order,true) "
                            "ON CONFLICT (code) DO NOTHING"
                        ),
                        row,
                    )
            if not settings.database_url.startswith("sqlite"):
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS sous_filiere VARCHAR(30)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS product_catalog_id INTEGER"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS attributes_json TEXT"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS wood_essence_id INTEGER"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS wood_form VARCHAR(40)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS volume_m3 NUMERIC(14,4)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS lot_number VARCHAR(120)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS traceability_id VARCHAR(120)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS origin_reference VARCHAR(160)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS previous_block_hash VARCHAR(64)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS current_block_hash VARCHAR(64)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS trace_payload_json TEXT"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS wood_classification VARCHAR(30)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS cites_laf_status VARCHAR(20)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS cites_ndf_status VARCHAR(20)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS cites_international_status VARCHAR(20)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS destruction_status VARCHAR(20)"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS destruction_requested_at TIMESTAMPTZ"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS destruction_validated_at TIMESTAMPTZ"))
                conn.execute(text("ALTER TABLE lots ADD COLUMN IF NOT EXISTS destruction_evidence_json TEXT"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS filiere VARCHAR(20)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS region_code VARCHAR(20)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS origin_reference VARCHAR(160)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS lot_references_json TEXT"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS quantity_total NUMERIC(14,4)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS unit VARCHAR(20)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS unit_price_avg NUMERIC(14,2)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS subtotal_ht NUMERIC(14,2)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS taxes_json TEXT"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS taxes_total NUMERIC(14,2)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_ttc NUMERIC(14,2)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_hash VARCHAR(64)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS previous_invoice_hash VARCHAR(64)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS internal_signature VARCHAR(64)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS trace_payload_json TEXT"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(80)"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS receipt_document_id INTEGER"))
                conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS is_immutable BOOLEAN DEFAULT TRUE"))

    return app


app = create_app()
