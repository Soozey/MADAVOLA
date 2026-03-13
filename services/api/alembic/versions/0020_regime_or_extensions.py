from alembic import op
import sqlalchemy as sa

revision = "0020_regime_or_extensions"
down_revision = "0019_actor_regime_or_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transformation_facilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("facility_type", sa.String(length=40), nullable=False),
        sa.Column("operator_actor_id", sa.Integer(), nullable=False),
        sa.Column("autorisation_ref", sa.String(length=120), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity_declared", sa.Numeric(14, 4), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["operator_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "transformation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lot_input_id", sa.Integer(), nullable=False),
        sa.Column("facility_id", sa.Integer(), nullable=False),
        sa.Column("quantity_input", sa.Numeric(14, 4), nullable=False),
        sa.Column("quantity_output", sa.Numeric(14, 4), nullable=False),
        sa.Column("perte_declared", sa.Numeric(14, 4), nullable=False),
        sa.Column("justificatif", sa.Text(), nullable=True),
        sa.Column("validated_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("output_lot_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["transformation_facilities.id"]),
        sa.ForeignKeyConstraint(["lot_input_id"], ["lots.id"]),
        sa.ForeignKeyConstraint(["output_lot_id"], ["lots.id"]),
        sa.ForeignKeyConstraint(["validated_by_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lot_test_certificates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=False),
        sa.Column("tested_by_actor_id", sa.Integer(), nullable=False),
        sa.Column("gross_weight", sa.Numeric(14, 4), nullable=False),
        sa.Column("purity", sa.Numeric(8, 4), nullable=False),
        sa.Column("certificate_number", sa.String(length=80), nullable=False),
        sa.Column("certificate_qr", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
        sa.ForeignKeyConstraint(["tested_by_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_number"),
        sa.UniqueConstraint("certificate_qr"),
    )
    op.create_table(
        "transport_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=False),
        sa.Column("transporter_actor_id", sa.Integer(), nullable=False),
        sa.Column("depart_actor_id", sa.Integer(), nullable=False),
        sa.Column("arrival_actor_id", sa.Integer(), nullable=False),
        sa.Column("depart_geo_point_id", sa.Integer(), nullable=False),
        sa.Column("arrival_geo_point_id", sa.Integer(), nullable=True),
        sa.Column("laissez_passer_document_id", sa.Integer(), nullable=True),
        sa.Column("depart_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["arrival_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["arrival_geo_point_id"], ["geo_points.id"]),
        sa.ForeignKeyConstraint(["depart_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["depart_geo_point_id"], ["geo_points.id"]),
        sa.ForeignKeyConstraint(["laissez_passer_document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
        sa.ForeignKeyConstraint(["transporter_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "export_validations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("export_id", sa.Integer(), nullable=False),
        sa.Column("validator_actor_id", sa.Integer(), nullable=False),
        sa.Column("validator_role", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["export_id"], ["export_dossiers.id"]),
        sa.ForeignKeyConstraint(["validator_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "forex_repatriations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("export_id", sa.Integer(), nullable=False),
        sa.Column("bank_actor_id", sa.Integer(), nullable=False),
        sa.Column("proof_document_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("repatriated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bank_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["export_id"], ["export_dossiers.id"]),
        sa.ForeignKeyConstraint(["proof_document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "export_checklist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("export_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(length=50), nullable=False),
        sa.Column("required", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["export_id"], ["export_dossiers.id"]),
        sa.ForeignKeyConstraint(["verified_by_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "legal_versioning",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filiere", sa.String(length=20), nullable=False),
        sa.Column("legal_key", sa.String(length=80), nullable=False),
        sa.Column("version_tag", sa.String(length=40), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_actor_id"], ["actors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tax_breakdowns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("taxable_event_type", sa.String(length=40), nullable=False),
        sa.Column("taxable_event_id", sa.String(length=80), nullable=False),
        sa.Column("legal_version_id", sa.Integer(), nullable=True),
        sa.Column("tax_type", sa.String(length=40), nullable=False),
        sa.Column("beneficiary_level", sa.String(length=20), nullable=False),
        sa.Column("beneficiary_id", sa.Integer(), nullable=True),
        sa.Column("base_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(12, 8), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("payment_request_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legal_version_id"], ["legal_versioning.id"]),
        sa.ForeignKeyConstraint(["payment_request_id"], ["payment_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tax_breakdowns_event", "tax_breakdowns", ["taxable_event_type", "taxable_event_id"])


def downgrade() -> None:
    op.drop_index("ix_tax_breakdowns_event", table_name="tax_breakdowns")
    op.drop_table("tax_breakdowns")
    op.drop_table("legal_versioning")
    op.drop_table("export_checklist_items")
    op.drop_table("forex_repatriations")
    op.drop_table("export_validations")
    op.drop_table("transport_events")
    op.drop_table("lot_test_certificates")
    op.drop_table("transformation_events")
    op.drop_table("transformation_facilities")
