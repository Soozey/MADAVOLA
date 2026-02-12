from alembic import op
import sqlalchemy as sa

revision = "0018_dtspm_tax_records"
down_revision = "0017_gold_journey_gap_fill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("taxable_event_type", sa.String(length=40), nullable=False),
        sa.Column("taxable_event_id", sa.String(length=80), nullable=False),
        sa.Column("tax_type", sa.String(length=40), nullable=False),
        sa.Column("beneficiary_level", sa.String(length=20), nullable=False),
        sa.Column("beneficiary_id", sa.Integer(), nullable=True),
        sa.Column("beneficiary_key", sa.String(length=40), nullable=False),
        sa.Column("base_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(12, 8), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("export_id", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attribution_note", sa.String(length=120), nullable=True),
        sa.Column("created_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_actor_id"], ["actors.id"]),
        sa.ForeignKeyConstraint(["export_id"], ["export_dossiers.id"]),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["trade_transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_tax_records_event", "tax_records", ["taxable_event_type", "taxable_event_id"])
    op.create_index("ix_tax_records_status", "tax_records", ["status"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_tax_records_active_event_beneficiary
        ON tax_records (
          taxable_event_type,
          taxable_event_id,
          tax_type,
          beneficiary_level,
          beneficiary_key
        )
        WHERE status IN ('DUE', 'PAID')
        """
    )


def downgrade() -> None:
    op.drop_index("uq_tax_records_active_event_beneficiary", table_name="tax_records")
    op.drop_index("ix_tax_records_status", table_name="tax_records")
    op.drop_index("ix_tax_records_event", table_name="tax_records")
    op.drop_table("tax_records")
