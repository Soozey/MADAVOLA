"""add actor kyc, wallet and commune profile tables

Revision ID: 0023_actor_kyc_wallet_commune_profile
Revises: 0022_emergency_alerts
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0023_actor_kyc_wallet_commune_profile"
down_revision = "0022_emergency_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actor_kyc",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("pieces", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("verified_by", sa.Integer(), sa.ForeignKey("actors.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_actor_kyc_actor_id", "actor_kyc", ["actor_id"])

    op.create_table(
        "actor_wallets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("operator_name", sa.String(length=80), nullable=True),
        sa.Column("account_ref", sa.String(length=120), nullable=False),
        sa.Column("is_primary", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_actor_wallets_actor_id", "actor_wallets", ["actor_id"])
    op.create_index("ix_actor_wallets_provider", "actor_wallets", ["provider"])

    op.create_table(
        "commune_profiles",
        sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), primary_key=True),
        sa.Column("mobile_money_account_ref", sa.String(length=120), nullable=True),
        sa.Column("receiver_name", sa.String(length=120), nullable=True),
        sa.Column("receiver_phone", sa.String(length=30), nullable=True),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("commune_profiles")
    op.drop_index("ix_actor_wallets_provider", table_name="actor_wallets")
    op.drop_index("ix_actor_wallets_actor_id", table_name="actor_wallets")
    op.drop_table("actor_wallets")
    op.drop_index("ix_actor_kyc_actor_id", table_name="actor_kyc")
    op.drop_table("actor_kyc")

