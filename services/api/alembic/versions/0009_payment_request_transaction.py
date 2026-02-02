from alembic import op
import sqlalchemy as sa

revision = "0009_payment_request_transaction"
down_revision = "0008_transactions_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payment_requests", sa.Column("transaction_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_payment_requests_transaction",
        "payment_requests",
        "trade_transactions",
        ["transaction_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_payment_requests_transaction", "payment_requests", type_="foreignkey")
    op.drop_column("payment_requests", "transaction_id")
