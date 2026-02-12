from alembic import op
import sqlalchemy as sa

revision = "0017_gold_journey_gap_fill"
down_revision = "0016_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lots", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("lots", sa.Column("photo_urls_json", sa.Text(), nullable=True))
    op.add_column("lots", sa.Column("qr_code", sa.String(length=255), nullable=True))
    op.add_column("lots", sa.Column("declaration_receipt_number", sa.String(length=80), nullable=True))
    op.add_column("lots", sa.Column("declaration_receipt_document_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_lots_declaration_receipt_document_id",
        "lots",
        "documents",
        ["declaration_receipt_document_id"],
        ["id"],
    )
    op.create_unique_constraint("uq_lots_qr_code", "lots", ["qr_code"])
    op.create_unique_constraint(
        "uq_lots_declaration_receipt_number", "lots", ["declaration_receipt_number"]
    )

    op.add_column(
        "payment_requests", sa.Column("beneficiary_label", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "payment_requests", sa.Column("beneficiary_msisdn", sa.String(length=32), nullable=True)
    )

    op.add_column("violation_cases", sa.Column("lot_action_status", sa.String(length=20), nullable=True))

    op.add_column("invoices", sa.Column("qr_code", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_invoices_qr_code", "invoices", ["qr_code"])

    op.add_column("export_dossiers", sa.Column("dossier_number", sa.String(length=50), nullable=True))
    op.add_column(
        "export_dossiers", sa.Column("destination_country", sa.String(length=100), nullable=True)
    )
    op.add_column("export_dossiers", sa.Column("transport_mode", sa.String(length=50), nullable=True))
    op.add_column("export_dossiers", sa.Column("declared_value", sa.Numeric(14, 2), nullable=True))
    op.add_column("export_dossiers", sa.Column("sealed_qr", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_export_dossiers_dossier_number", "export_dossiers", ["dossier_number"])


def downgrade() -> None:
    op.drop_constraint("uq_export_dossiers_dossier_number", "export_dossiers", type_="unique")
    op.drop_column("export_dossiers", "sealed_qr")
    op.drop_column("export_dossiers", "declared_value")
    op.drop_column("export_dossiers", "transport_mode")
    op.drop_column("export_dossiers", "destination_country")
    op.drop_column("export_dossiers", "dossier_number")

    op.drop_constraint("uq_invoices_qr_code", "invoices", type_="unique")
    op.drop_column("invoices", "qr_code")

    op.drop_column("violation_cases", "lot_action_status")

    op.drop_column("payment_requests", "beneficiary_msisdn")
    op.drop_column("payment_requests", "beneficiary_label")

    op.drop_constraint("uq_lots_declaration_receipt_number", "lots", type_="unique")
    op.drop_constraint("uq_lots_qr_code", "lots", type_="unique")
    op.drop_constraint(
        "fk_lots_declaration_receipt_document_id", "lots", type_="foreignkey"
    )
    op.drop_column("lots", "declaration_receipt_document_id")
    op.drop_column("lots", "declaration_receipt_number")
    op.drop_column("lots", "qr_code")
    op.drop_column("lots", "photo_urls_json")
    op.drop_column("lots", "notes")
