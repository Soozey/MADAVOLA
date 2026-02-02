from alembic import op
import sqlalchemy as sa

revision = "0011_lots_ledger"
down_revision = "0010_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filiere", sa.String(length=20), nullable=False),
        sa.Column("product_type", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("declared_by_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("current_owner_actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("declare_geo_point_id", sa.Integer(), sa.ForeignKey("geo_points.id"), nullable=False),
        sa.Column("parent_lot_id", sa.Integer(), sa.ForeignKey("lots.id")),
    )
    op.create_table(
        "lot_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("child_lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("relation_type", sa.String(length=20), nullable=False),
        sa.Column("quantity_from_child", sa.Numeric(14, 4), nullable=False),
    )
    op.create_table(
        "inventory_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id"), nullable=False),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(14, 4), nullable=False),
        sa.Column("ref_event_type", sa.String(length=50), nullable=False),
        sa.Column("ref_event_id", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("inventory_ledger")
    op.drop_table("lot_links")
    op.drop_table("lots")
