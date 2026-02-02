from alembic import op
import sqlalchemy as sa

revision = "0002_auth_actor"
down_revision = "0001_territory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type_personne", sa.String(length=20), nullable=False),
        sa.Column("nom", sa.String(length=150), nullable=False),
        sa.Column("prenoms", sa.String(length=150)),
        sa.Column("telephone", sa.String(length=30), unique=True),
        sa.Column("email", sa.String(length=255), unique=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "actor_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_to", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "actor_auth",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("token_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("actor_auth")
    op.drop_table("actor_roles")
    op.drop_table("actors")
