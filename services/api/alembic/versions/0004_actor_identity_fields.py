from alembic import op
import sqlalchemy as sa

revision = "0004_actor_identity_fields"
down_revision = "0003_geo_actor_signup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("actors", sa.Column("cin", sa.String(length=50)))
    op.add_column("actors", sa.Column("nif", sa.String(length=50)))
    op.add_column("actors", sa.Column("stat", sa.String(length=50)))
    op.add_column("actors", sa.Column("rccm", sa.String(length=50)))


def downgrade() -> None:
    op.drop_column("actors", "rccm")
    op.drop_column("actors", "stat")
    op.drop_column("actors", "nif")
    op.drop_column("actors", "cin")
