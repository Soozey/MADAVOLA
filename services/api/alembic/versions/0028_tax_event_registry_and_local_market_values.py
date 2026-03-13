"""tax event registry + local market values

Revision ID: 0028_tax_event_registry_and_local_market_values
Revises: 0027_invoice_bois_cites_enhancements
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0028_tax_event_registry_and_local_market_values"
down_revision = "0027_invoice_bois_cites_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(table: str) -> bool:
        return table in inspector.get_table_names()

    def has_index(table: str, index_name: str) -> bool:
        try:
            return any(idx.get("name") == index_name for idx in inspector.get_indexes(table))
        except Exception:
            return False

    if not has_table("local_market_values"):
        op.create_table(
            "local_market_values",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("filiere", sa.String(length=20), nullable=False, server_default="OR"),
            sa.Column("substance", sa.String(length=40), nullable=False, server_default="OR"),
            sa.Column("region_code", sa.String(length=20), nullable=True),
            sa.Column("commune_code", sa.String(length=20), nullable=True),
            sa.Column("unit", sa.String(length=20), nullable=False, server_default="kg"),
            sa.Column("value_per_unit", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="MGA"),
            sa.Column("legal_reference", sa.String(length=255), nullable=False),
            sa.Column("version_tag", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by_actor_id"], ["actors.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)
    if has_table("local_market_values") and not has_index("local_market_values", "ix_local_market_values_lookup"):
        op.create_index(
            "ix_local_market_values_lookup",
            "local_market_values",
            ["filiere", "substance", "status", "effective_from"],
        )
        inspector = sa.inspect(bind)

    if not has_table("tax_event_registry"):
        op.create_table(
            "tax_event_registry",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("taxable_event_type", sa.String(length=40), nullable=False),
            sa.Column("taxable_event_id", sa.String(length=80), nullable=False),
            sa.Column("anti_double_key", sa.String(length=96), nullable=False),
            sa.Column("period_key", sa.String(length=20), nullable=True),
            sa.Column("reference_transaction", sa.String(length=80), nullable=True),
            sa.Column("filiere", sa.String(length=20), nullable=False, server_default="OR"),
            sa.Column("region_code", sa.String(length=20), nullable=True),
            sa.Column("assiette_mode", sa.String(length=30), nullable=False, server_default="manual"),
            sa.Column("assiette_reference", sa.String(length=160), nullable=True),
            sa.Column("base_amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="MGA"),
            sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("abatement_rate", sa.Numeric(12, 8), nullable=False, server_default="0"),
            sa.Column("abatement_reason", sa.String(length=180), nullable=True),
            sa.Column("legal_basis_json", sa.Text(), nullable=True),
            sa.Column("legal_version_id", sa.Integer(), nullable=True),
            sa.Column("payer_actor_id", sa.Integer(), nullable=True),
            sa.Column("payer_role_code", sa.String(length=60), nullable=True),
            sa.Column("lot_id", sa.Integer(), nullable=True),
            sa.Column("export_id", sa.Integer(), nullable=True),
            sa.Column("transaction_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="DUE"),
            sa.Column("invoice_number", sa.String(length=80), nullable=True),
            sa.Column("invoice_document_id", sa.Integer(), nullable=True),
            sa.Column("receipt_number", sa.String(length=80), nullable=True),
            sa.Column("receipt_document_id", sa.Integer(), nullable=True),
            sa.Column("payment_request_id", sa.Integer(), nullable=True),
            sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["legal_version_id"], ["legal_versioning.id"]),
            sa.ForeignKeyConstraint(["payer_actor_id"], ["actors.id"]),
            sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
            sa.ForeignKeyConstraint(["export_id"], ["export_dossiers.id"]),
            sa.ForeignKeyConstraint(["transaction_id"], ["trade_transactions.id"]),
            sa.ForeignKeyConstraint(["invoice_document_id"], ["documents.id"]),
            sa.ForeignKeyConstraint(["receipt_document_id"], ["documents.id"]),
            sa.ForeignKeyConstraint(["payment_request_id"], ["payment_requests.id"]),
            sa.ForeignKeyConstraint(["created_by_actor_id"], ["actors.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("anti_double_key", name="uq_tax_event_registry_anti_double_key"),
            sa.UniqueConstraint("invoice_number", name="uq_tax_event_registry_invoice_number"),
            sa.UniqueConstraint("receipt_number", name="uq_tax_event_registry_receipt_number"),
        )
        inspector = sa.inspect(bind)
    if has_table("tax_event_registry") and not has_index("tax_event_registry", "ix_tax_event_registry_event"):
        op.create_index(
            "ix_tax_event_registry_event",
            "tax_event_registry",
            ["taxable_event_type", "taxable_event_id"],
        )
        inspector = sa.inspect(bind)
    if has_table("tax_event_registry") and not has_index("tax_event_registry", "ix_tax_event_registry_status"):
        op.create_index(
            "ix_tax_event_registry_status",
            "tax_event_registry",
            ["status"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(table: str) -> bool:
        return table in inspector.get_table_names()

    def has_index(table: str, index_name: str) -> bool:
        try:
            return any(idx.get("name") == index_name for idx in inspector.get_indexes(table))
        except Exception:
            return False

    if has_table("tax_event_registry") and has_index("tax_event_registry", "ix_tax_event_registry_status"):
        op.drop_index("ix_tax_event_registry_status", table_name="tax_event_registry")
        inspector = sa.inspect(bind)
    if has_table("tax_event_registry") and has_index("tax_event_registry", "ix_tax_event_registry_event"):
        op.drop_index("ix_tax_event_registry_event", table_name="tax_event_registry")
        inspector = sa.inspect(bind)
    if has_table("tax_event_registry"):
        op.drop_table("tax_event_registry")
        inspector = sa.inspect(bind)
    if has_table("local_market_values") and has_index("local_market_values", "ix_local_market_values_lookup"):
        op.drop_index("ix_local_market_values_lookup", table_name="local_market_values")
        inspector = sa.inspect(bind)
    if has_table("local_market_values"):
        op.drop_table("local_market_values")
