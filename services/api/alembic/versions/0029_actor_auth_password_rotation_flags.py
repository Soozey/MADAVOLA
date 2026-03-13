"""actor auth password rotation flags

Revision ID: 0029_actor_auth_password_rotation_flags
Revises: 0028_tax_event_registry_and_local_market_values
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0029_actor_auth_password_rotation_flags"
down_revision = "0028_tax_event_registry_and_local_market_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("actor_auth")}

    if "must_change_password" not in columns:
        op.add_column(
            "actor_auth",
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "password_changed_at" not in columns:
        op.add_column(
            "actor_auth",
            sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "last_login_at" not in columns:
        op.add_column(
            "actor_auth",
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        )

    op.execute("UPDATE actor_auth SET must_change_password = 0 WHERE must_change_password IS NULL")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("actor_auth")}

    if "last_login_at" in columns:
        op.drop_column("actor_auth", "last_login_at")
    if "password_changed_at" in columns:
        op.drop_column("actor_auth", "password_changed_at")
    if "must_change_password" in columns:
        op.drop_column("actor_auth", "must_change_password")
