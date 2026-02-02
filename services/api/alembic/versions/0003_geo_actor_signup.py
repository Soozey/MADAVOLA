from alembic import op
import sqlalchemy as sa

revision = "0003_geo_actor_signup"
down_revision = "0002_auth_actor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "geo_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lat", sa.Numeric(9, 6), nullable=False),
        sa.Column("lon", sa.Numeric(9, 6), nullable=False),
        sa.Column("accuracy_m", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("device_id", sa.String(length=100)),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("actors.id")),
    )

    op.add_column("actors", sa.Column("region_id", sa.Integer(), nullable=False))
    op.add_column("actors", sa.Column("district_id", sa.Integer(), nullable=False))
    op.add_column("actors", sa.Column("commune_id", sa.Integer(), nullable=False))
    op.add_column("actors", sa.Column("fokontany_id", sa.Integer(), nullable=True))
    op.add_column("actors", sa.Column("territory_version_id", sa.Integer(), nullable=False))
    op.add_column("actors", sa.Column("signup_geo_point_id", sa.Integer(), nullable=True))

    op.create_foreign_key("fk_actors_region", "actors", "regions", ["region_id"], ["id"])
    op.create_foreign_key("fk_actors_district", "actors", "districts", ["district_id"], ["id"])
    op.create_foreign_key("fk_actors_commune", "actors", "communes", ["commune_id"], ["id"])
    op.create_foreign_key("fk_actors_fokontany", "actors", "fokontany", ["fokontany_id"], ["id"])
    op.create_foreign_key(
        "fk_actors_territory_version",
        "actors",
        "territory_versions",
        ["territory_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_actors_geo_point",
        "actors",
        "geo_points",
        ["signup_geo_point_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_actors_geo_point", "actors", type_="foreignkey")
    op.drop_constraint("fk_actors_territory_version", "actors", type_="foreignkey")
    op.drop_constraint("fk_actors_fokontany", "actors", type_="foreignkey")
    op.drop_constraint("fk_actors_commune", "actors", type_="foreignkey")
    op.drop_constraint("fk_actors_district", "actors", type_="foreignkey")
    op.drop_constraint("fk_actors_region", "actors", type_="foreignkey")
    op.drop_column("actors", "signup_geo_point_id")
    op.drop_column("actors", "territory_version_id")
    op.drop_column("actors", "fokontany_id")
    op.drop_column("actors", "commune_id")
    op.drop_column("actors", "district_id")
    op.drop_column("actors", "region_id")
    op.drop_table("geo_points")
