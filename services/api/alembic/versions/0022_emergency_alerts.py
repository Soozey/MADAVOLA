"""add emergency alerts table

Revision ID: 0022_emergency_alerts
Revises: 0021_rbac_role_catalog
Create Date: 2026-02-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_emergency_alerts"
down_revision = "0021_rbac_role_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emergency_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("target_service", sa.String(length=20), nullable=False, server_default="both"),
        sa.Column("filiere", sa.String(length=20), nullable=True),
        sa.Column("role_code", sa.String(length=50), nullable=True),
        sa.Column("geo_point_id", sa.Integer(), sa.ForeignKey("geo_points.id"), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="high"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("handled_by_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_emergency_alerts_actor_id", "emergency_alerts", ["actor_id"])
    op.create_index("ix_emergency_alerts_status", "emergency_alerts", ["status"])
    op.create_index("ix_emergency_alerts_target_service", "emergency_alerts", ["target_service"])


def downgrade() -> None:
    op.drop_index("ix_emergency_alerts_target_service", table_name="emergency_alerts")
    op.drop_index("ix_emergency_alerts_status", table_name="emergency_alerts")
    op.drop_index("ix_emergency_alerts_actor_id", table_name="emergency_alerts")
    op.drop_table("emergency_alerts")

