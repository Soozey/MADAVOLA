from alembic import op
import sqlalchemy as sa

revision = "0014_export_improvements"
down_revision = "0013_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("export_dossiers", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    
    op.create_table(
        "export_lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("export_dossier_id", sa.Integer(), sa.ForeignKey("export_dossiers.id"), nullable=False),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("quantity_in_export", sa.Numeric(14, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("export_lots")
    op.drop_column("export_dossiers", "updated_at")
