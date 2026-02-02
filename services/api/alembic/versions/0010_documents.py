from alembic import op
import sqlalchemy as sa

revision = "0010_documents"
down_revision = "0009_payment_request_transaction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doc_type", sa.String(length=30), nullable=False),
        sa.Column("owner_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("related_entity_type", sa.String(length=50)),
        sa.Column("related_entity_id", sa.String(length=50)),
        sa.Column("storage_path", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("documents")
