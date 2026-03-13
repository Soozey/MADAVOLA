"""messages and marketplace tables

Revision ID: 0030_messages_marketplace
Revises: 0029_actor_auth_password_rotation_flags
Create Date: 2026-02-26 15:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0030_messages_marketplace"
down_revision = "0029_actor_auth_password_rotation_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "contact_requests" not in existing_tables:
        op.create_table(
            "contact_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("requester_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
            sa.Column("target_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        )
    existing_contact_idx = {idx["name"] for idx in inspector.get_indexes("contact_requests")} if "contact_requests" in set(inspector.get_table_names()) else set()
    if "ix_contact_requests_requester_actor_id" not in existing_contact_idx:
        op.create_index("ix_contact_requests_requester_actor_id", "contact_requests", ["requester_actor_id"])
    if "ix_contact_requests_target_actor_id" not in existing_contact_idx:
        op.create_index("ix_contact_requests_target_actor_id", "contact_requests", ["target_actor_id"])

    if "direct_messages" not in set(inspector.get_table_names()):
        op.create_table(
            "direct_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("contact_request_id", sa.Integer(), sa.ForeignKey("contact_requests.id"), nullable=True),
            sa.Column("sender_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
            sa.Column("receiver_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        )
    existing_msg_idx = {idx["name"] for idx in inspector.get_indexes("direct_messages")} if "direct_messages" in set(inspector.get_table_names()) else set()
    if "ix_direct_messages_sender_actor_id" not in existing_msg_idx:
        op.create_index("ix_direct_messages_sender_actor_id", "direct_messages", ["sender_actor_id"])
    if "ix_direct_messages_receiver_actor_id" not in existing_msg_idx:
        op.create_index("ix_direct_messages_receiver_actor_id", "direct_messages", ["receiver_actor_id"])

    if "marketplace_offers" not in set(inspector.get_table_names()):
        op.create_table(
            "marketplace_offers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
            sa.Column("offer_type", sa.String(length=20), nullable=False),
            sa.Column("filiere", sa.String(length=20), nullable=False),
            sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=True),
            sa.Column("product_type", sa.String(length=60), nullable=False),
            sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
            sa.Column("unit", sa.String(length=20), nullable=False),
            sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="MGA"),
            sa.Column("location_commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    existing_market_idx = {idx["name"] for idx in inspector.get_indexes("marketplace_offers")} if "marketplace_offers" in set(inspector.get_table_names()) else set()
    if "ix_marketplace_offers_actor_id" not in existing_market_idx:
        op.create_index("ix_marketplace_offers_actor_id", "marketplace_offers", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_offers_actor_id", table_name="marketplace_offers")
    op.drop_table("marketplace_offers")

    op.drop_index("ix_direct_messages_receiver_actor_id", table_name="direct_messages")
    op.drop_index("ix_direct_messages_sender_actor_id", table_name="direct_messages")
    op.drop_table("direct_messages")

    op.drop_index("ix_contact_requests_target_actor_id", table_name="contact_requests")
    op.drop_index("ix_contact_requests_requester_actor_id", table_name="contact_requests")
    op.drop_table("contact_requests")
