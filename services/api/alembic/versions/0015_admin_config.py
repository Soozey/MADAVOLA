from alembic import op
import sqlalchemy as sa

revision = "0015_admin_config"
down_revision = "0014_export_improvements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("value", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("updated_by_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_config")
