"""add destination commune on export dossier

Revision ID: 0024_export_destination_commune
Revises: 0023_actor_kyc_wallet_commune_profile
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_export_destination_commune"
down_revision = "0023_actor_kyc_wallet_commune_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("export_dossiers", sa.Column("destination_commune_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_export_dossiers_destination_commune_id",
        "export_dossiers",
        "communes",
        ["destination_commune_id"],
        ["id"],
    )
    op.create_index("ix_export_dossiers_destination_commune_id", "export_dossiers", ["destination_commune_id"])


def downgrade() -> None:
    op.drop_index("ix_export_dossiers_destination_commune_id", table_name="export_dossiers")
    op.drop_constraint("fk_export_dossiers_destination_commune_id", "export_dossiers", type_="foreignkey")
    op.drop_column("export_dossiers", "destination_commune_id")

