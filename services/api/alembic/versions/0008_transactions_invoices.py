from alembic import op
import sqlalchemy as sa

revision = "0008_transactions_invoices"
down_revision = "0007_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trade_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("buyer_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "trade_transaction_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("trade_transactions.id"),
            nullable=False,
        ),
        sa.Column("lot_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_amount", sa.Numeric(14, 2), nullable=False),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("trade_transactions.id"),
            nullable=False,
        ),
        sa.Column("seller_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("buyer_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("trade_transaction_items")
    op.drop_table("trade_transactions")
