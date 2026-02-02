from alembic import op
import sqlalchemy as sa

revision = "0005_payments"
down_revision = "0004_actor_identity_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("config_json", sa.Text()),
    )

    op.create_table(
        "payment_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("payment_providers.id"), nullable=False),
        sa.Column("payer_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("payee_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("external_ref", sa.String(length=80), nullable=False, unique=True),
        sa.Column("idempotency_key", sa.String(length=80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "payment_request_id",
            sa.Integer(),
            sa.ForeignKey("payment_requests.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("operator_ref", sa.String(length=120)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "webhook_inbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("payment_providers.id"), nullable=False),
        sa.Column("external_ref", sa.String(length=80), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
    )
    op.create_unique_constraint(
        "uq_webhook_inbox_provider_ref",
        "webhook_inbox",
        ["provider_id", "external_ref"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_webhook_inbox_provider_ref", "webhook_inbox", type_="unique")
    op.drop_table("webhook_inbox")
    op.drop_table("payments")
    op.drop_table("payment_requests")
    op.drop_table("payment_providers")
