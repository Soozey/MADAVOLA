from alembic import op
import sqlalchemy as sa

revision = "0012_inspections_penalties"
down_revision = "0011_lots_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inspections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inspector_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("inspected_actor_id", sa.Integer(), sa.ForeignKey("actors.id")),
        sa.Column("inspected_lot_id", sa.Integer(), sa.ForeignKey("lots.id")),
        sa.Column("inspected_invoice_id", sa.Integer(), sa.ForeignKey("invoices.id")),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("reason_code", sa.String(length=50)),
        sa.Column("notes", sa.String(length=255)),
        sa.Column("geo_point_id", sa.Integer(), sa.ForeignKey("geo_points.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "violation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inspection_id", sa.Integer(), sa.ForeignKey("inspections.id"), nullable=False),
        sa.Column("violation_type", sa.String(length=50), nullable=False),
        sa.Column("legal_basis_ref", sa.String(length=100)),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "penalties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("violation_case_id", sa.Integer(), sa.ForeignKey("violation_cases.id"), nullable=False),
        sa.Column("penalty_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2)),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("executed_by_actor_id", sa.Integer(), sa.ForeignKey("actors.id")),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("penalties")
    op.drop_table("violation_cases")
    op.drop_table("inspections")
