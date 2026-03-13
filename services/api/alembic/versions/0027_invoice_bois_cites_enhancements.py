"""invoice structure + bois cites/classification enhancements

Revision ID: 0027_invoice_bois_cites_enhancements
Revises: 0026_lot_traceability_chain
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0027_invoice_bois_cites_enhancements"
down_revision = "0026_lot_traceability_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_column(table: str, column: str) -> bool:
        cols = inspector.get_columns(table)
        return any(col["name"] == column for col in cols)

    def add_column_if_missing(table: str, column: sa.Column) -> None:
        if not has_column(table, column.name):
            op.add_column(table, column)

    add_column_if_missing("invoices", sa.Column("filiere", sa.String(length=20), nullable=True))
    add_column_if_missing("invoices", sa.Column("region_code", sa.String(length=20), nullable=True))
    add_column_if_missing("invoices", sa.Column("origin_reference", sa.String(length=160), nullable=True))
    add_column_if_missing("invoices", sa.Column("lot_references_json", sa.Text(), nullable=True))
    add_column_if_missing("invoices", sa.Column("quantity_total", sa.Numeric(14, 4), nullable=True))
    add_column_if_missing("invoices", sa.Column("unit", sa.String(length=20), nullable=True))
    add_column_if_missing("invoices", sa.Column("unit_price_avg", sa.Numeric(14, 2), nullable=True))
    add_column_if_missing("invoices", sa.Column("subtotal_ht", sa.Numeric(14, 2), nullable=True))
    add_column_if_missing("invoices", sa.Column("taxes_json", sa.Text(), nullable=True))
    add_column_if_missing("invoices", sa.Column("taxes_total", sa.Numeric(14, 2), nullable=True))
    add_column_if_missing("invoices", sa.Column("total_ttc", sa.Numeric(14, 2), nullable=True))
    add_column_if_missing("invoices", sa.Column("invoice_hash", sa.String(length=64), nullable=True))
    add_column_if_missing("invoices", sa.Column("previous_invoice_hash", sa.String(length=64), nullable=True))
    add_column_if_missing("invoices", sa.Column("internal_signature", sa.String(length=64), nullable=True))
    add_column_if_missing("invoices", sa.Column("trace_payload_json", sa.Text(), nullable=True))
    add_column_if_missing("invoices", sa.Column("receipt_number", sa.String(length=80), nullable=True))
    add_column_if_missing("invoices", sa.Column("receipt_document_id", sa.Integer(), nullable=True))
    add_column_if_missing("invoices", sa.Column("is_immutable", sa.Boolean(), nullable=False, server_default=sa.true()))

    if bind.dialect.name != "sqlite":
        fk_names = {fk.get("name") for fk in inspector.get_foreign_keys("invoices")}
        if "fk_invoices_receipt_document_id" not in fk_names:
            op.create_foreign_key(
                "fk_invoices_receipt_document_id",
                "invoices",
                "documents",
                ["receipt_document_id"],
                ["id"],
            )

    add_column_if_missing("lots", sa.Column("wood_classification", sa.String(length=30), nullable=True))
    add_column_if_missing("lots", sa.Column("cites_laf_status", sa.String(length=20), nullable=True))
    add_column_if_missing("lots", sa.Column("cites_ndf_status", sa.String(length=20), nullable=True))
    add_column_if_missing("lots", sa.Column("cites_international_status", sa.String(length=20), nullable=True))
    add_column_if_missing("lots", sa.Column("destruction_status", sa.String(length=20), nullable=True))
    add_column_if_missing("lots", sa.Column("destruction_requested_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("lots", sa.Column("destruction_validated_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("lots", sa.Column("destruction_evidence_json", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_column(table: str, column: str) -> bool:
        cols = inspector.get_columns(table)
        return any(col["name"] == column for col in cols)

    for column in [
        "destruction_evidence_json",
        "destruction_validated_at",
        "destruction_requested_at",
        "destruction_status",
        "cites_international_status",
        "cites_ndf_status",
        "cites_laf_status",
        "wood_classification",
    ]:
        if has_column("lots", column):
            op.drop_column("lots", column)

    if bind.dialect.name != "sqlite":
        fk_names = {fk.get("name") for fk in inspector.get_foreign_keys("invoices")}
        if "fk_invoices_receipt_document_id" in fk_names:
            op.drop_constraint("fk_invoices_receipt_document_id", "invoices", type_="foreignkey")

    for column in [
        "is_immutable",
        "receipt_document_id",
        "receipt_number",
        "trace_payload_json",
        "internal_signature",
        "previous_invoice_hash",
        "invoice_hash",
        "total_ttc",
        "taxes_total",
        "taxes_json",
        "subtotal_ht",
        "unit_price_avg",
        "unit",
        "quantity_total",
        "lot_references_json",
        "origin_reference",
        "region_code",
        "filiere",
    ]:
        if has_column("invoices", column):
            op.drop_column("invoices", column)
