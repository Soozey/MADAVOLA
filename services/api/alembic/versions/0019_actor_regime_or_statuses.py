from alembic import op
import sqlalchemy as sa

revision = "0019_actor_regime_or_statuses"
down_revision = "0018_dtspm_tax_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("actors", sa.Column("laissez_passer_access_status", sa.String(length=20), nullable=False, server_default="active"))
    op.add_column("actors", sa.Column("agrement_status", sa.String(length=20), nullable=False, server_default="active"))
    op.add_column("actors", sa.Column("sig_oc_access_status", sa.String(length=20), nullable=False, server_default="active"))

    op.alter_column("actors", "laissez_passer_access_status", server_default=None)
    op.alter_column("actors", "agrement_status", server_default=None)
    op.alter_column("actors", "sig_oc_access_status", server_default=None)


def downgrade() -> None:
    op.drop_column("actors", "sig_oc_access_status")
    op.drop_column("actors", "agrement_status")
    op.drop_column("actors", "laissez_passer_access_status")
