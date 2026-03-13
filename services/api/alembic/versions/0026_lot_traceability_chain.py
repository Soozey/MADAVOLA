"""lot traceability numbering and lightweight hash chain

Revision ID: 0026_lot_traceability_chain
Revises: 0025_card_workflow_enhancements
Create Date: 2026-02-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_lot_traceability_chain"
down_revision = "0025_card_workflow_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lots", sa.Column("lot_number", sa.String(length=120), nullable=True))
    op.add_column("lots", sa.Column("traceability_id", sa.String(length=120), nullable=True))
    op.add_column("lots", sa.Column("origin_reference", sa.String(length=160), nullable=True))
    op.add_column("lots", sa.Column("previous_block_hash", sa.String(length=64), nullable=True))
    op.add_column("lots", sa.Column("current_block_hash", sa.String(length=64), nullable=True))
    op.add_column("lots", sa.Column("trace_payload_json", sa.Text(), nullable=True))
    op.create_index("ix_lots_lot_number", "lots", ["lot_number"], unique=True)
    op.create_index("ix_lots_traceability_id", "lots", ["traceability_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_lots_traceability_id", table_name="lots")
    op.drop_index("ix_lots_lot_number", table_name="lots")
    op.drop_column("lots", "trace_payload_json")
    op.drop_column("lots", "current_block_hash")
    op.drop_column("lots", "previous_block_hash")
    op.drop_column("lots", "origin_reference")
    op.drop_column("lots", "traceability_id")
    op.drop_column("lots", "lot_number")
