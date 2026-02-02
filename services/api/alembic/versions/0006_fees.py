from alembic import op
import sqlalchemy as sa

revision = "0006_fees"
down_revision = "0005_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fee_type", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
    )

    op.add_column("payment_requests", sa.Column("fee_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_payment_requests_fee",
        "payment_requests",
        "fees",
        ["fee_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_payment_requests_fee", "payment_requests", type_="foreignkey")
    op.drop_column("payment_requests", "fee_id")
    op.drop_table("fees")
