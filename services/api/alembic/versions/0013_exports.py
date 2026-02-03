from alembic import op
import sqlalchemy as sa

revision = "0013_exports"
down_revision = "0012_inspections_penalties"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "export_dossiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("destination", sa.String(length=100)),
        sa.Column("total_weight", sa.Numeric(14, 4)),
        sa.Column("created_by_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("export_dossiers")
