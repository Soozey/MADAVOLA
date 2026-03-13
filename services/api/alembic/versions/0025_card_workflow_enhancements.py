"""card workflow enhancements (identity, qr signature, receipts)

Revision ID: 0025_card_workflow_enhancements
Revises: 0024_export_destination_commune
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0025_card_workflow_enhancements"
down_revision = "0024_export_destination_commune"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("actors", sa.Column("surnom", sa.String(length=120), nullable=True))
    op.add_column("actors", sa.Column("date_naissance", sa.Date(), nullable=True))
    op.add_column("actors", sa.Column("cin_date_delivrance", sa.Date(), nullable=True))
    op.add_column("actors", sa.Column("adresse_text", sa.Text(), nullable=True))
    op.add_column("actors", sa.Column("photo_profile_url", sa.String(length=255), nullable=True))

    op.add_column("fees", sa.Column("receipt_number", sa.String(length=80), nullable=True))
    op.add_column("fees", sa.Column("receipt_document_id", sa.Integer(), nullable=True))
    op.create_index("ix_fees_receipt_number", "fees", ["receipt_number"], unique=True)

    op.add_column("kara_bolamena_cards", sa.Column("card_uid", sa.String(length=80), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("card_number", sa.String(length=120), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("validated_by_actor_id", sa.Integer(), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("front_document_id", sa.Integer(), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("back_document_id", sa.Integer(), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("qr_payload_json", sa.Text(), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("qr_payload_hash", sa.String(length=64), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("qr_signature", sa.String(length=128), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("qr_value", sa.String(length=255), nullable=True))
    op.add_column("kara_bolamena_cards", sa.Column("card_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_kara_bolamena_cards_card_uid", "kara_bolamena_cards", ["card_uid"], unique=True)
    op.create_index("ix_kara_bolamena_cards_card_number", "kara_bolamena_cards", ["card_number"], unique=True)

    op.add_column("collector_cards", sa.Column("card_uid", sa.String(length=80), nullable=True))
    op.add_column("collector_cards", sa.Column("card_number", sa.String(length=120), nullable=True))
    op.add_column("collector_cards", sa.Column("validated_by_actor_id", sa.Integer(), nullable=True))
    op.add_column("collector_cards", sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("collector_cards", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("collector_cards", sa.Column("front_document_id", sa.Integer(), nullable=True))
    op.add_column("collector_cards", sa.Column("back_document_id", sa.Integer(), nullable=True))
    op.add_column("collector_cards", sa.Column("qr_payload_json", sa.Text(), nullable=True))
    op.add_column("collector_cards", sa.Column("qr_payload_hash", sa.String(length=64), nullable=True))
    op.add_column("collector_cards", sa.Column("qr_signature", sa.String(length=128), nullable=True))
    op.add_column("collector_cards", sa.Column("qr_value", sa.String(length=255), nullable=True))
    op.add_column("collector_cards", sa.Column("card_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_collector_cards_card_uid", "collector_cards", ["card_uid"], unique=True)
    op.create_index("ix_collector_cards_card_number", "collector_cards", ["card_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_collector_cards_card_number", table_name="collector_cards")
    op.drop_index("ix_collector_cards_card_uid", table_name="collector_cards")
    op.drop_column("collector_cards", "card_version")
    op.drop_column("collector_cards", "qr_value")
    op.drop_column("collector_cards", "qr_signature")
    op.drop_column("collector_cards", "qr_payload_hash")
    op.drop_column("collector_cards", "qr_payload_json")
    op.drop_column("collector_cards", "back_document_id")
    op.drop_column("collector_cards", "front_document_id")
    op.drop_column("collector_cards", "revoked_at")
    op.drop_column("collector_cards", "validated_at")
    op.drop_column("collector_cards", "validated_by_actor_id")
    op.drop_column("collector_cards", "card_number")
    op.drop_column("collector_cards", "card_uid")

    op.drop_index("ix_kara_bolamena_cards_card_number", table_name="kara_bolamena_cards")
    op.drop_index("ix_kara_bolamena_cards_card_uid", table_name="kara_bolamena_cards")
    op.drop_column("kara_bolamena_cards", "card_version")
    op.drop_column("kara_bolamena_cards", "qr_value")
    op.drop_column("kara_bolamena_cards", "qr_signature")
    op.drop_column("kara_bolamena_cards", "qr_payload_hash")
    op.drop_column("kara_bolamena_cards", "qr_payload_json")
    op.drop_column("kara_bolamena_cards", "back_document_id")
    op.drop_column("kara_bolamena_cards", "front_document_id")
    op.drop_column("kara_bolamena_cards", "revoked_at")
    op.drop_column("kara_bolamena_cards", "validated_at")
    op.drop_column("kara_bolamena_cards", "validated_by_actor_id")
    op.drop_column("kara_bolamena_cards", "card_number")
    op.drop_column("kara_bolamena_cards", "card_uid")

    op.drop_index("ix_fees_receipt_number", table_name="fees")
    op.drop_column("fees", "receipt_document_id")
    op.drop_column("fees", "receipt_number")

    op.drop_column("actors", "photo_profile_url")
    op.drop_column("actors", "adresse_text")
    op.drop_column("actors", "cin_date_delivrance")
    op.drop_column("actors", "date_naissance")
    op.drop_column("actors", "surnom")
