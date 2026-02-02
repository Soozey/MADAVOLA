from alembic import op
import sqlalchemy as sa

revision = "0001_territory"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "territory_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_tag", sa.String(length=50), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("version_tag", name="uq_territory_versions_version_tag"),
    )

    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("territory_versions.id"), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("name_normalized", sa.String(length=150), nullable=False),
        sa.UniqueConstraint("version_id", "code", name="uq_regions_version_code"),
        sa.UniqueConstraint("version_id", "name_normalized", name="uq_regions_version_name"),
    )

    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("territory_versions.id"), nullable=False),
        sa.Column("region_id", sa.Integer(), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("name_normalized", sa.String(length=150), nullable=False),
        sa.UniqueConstraint(
            "version_id", "region_id", "code", name="uq_districts_version_region_code"
        ),
        sa.UniqueConstraint(
            "version_id",
            "region_id",
            "name_normalized",
            name="uq_districts_version_region_name",
        ),
    )
    op.create_index(
        "ix_districts_version_region",
        "districts",
        ["version_id", "region_id"],
    )

    op.create_table(
        "communes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("territory_versions.id"), nullable=False),
        sa.Column("district_id", sa.Integer(), sa.ForeignKey("districts.id"), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("name_normalized", sa.String(length=150), nullable=False),
        sa.Column("mobile_money_msisdn", sa.String(length=32)),
        sa.Column("latitude", sa.String(length=30)),
        sa.Column("longitude", sa.String(length=30)),
        sa.UniqueConstraint(
            "version_id", "district_id", "code", name="uq_communes_version_district_code"
        ),
        sa.UniqueConstraint(
            "version_id",
            "district_id",
            "name_normalized",
            name="uq_communes_version_district_name",
        ),
    )
    op.create_index(
        "ix_communes_version_district",
        "communes",
        ["version_id", "district_id"],
    )

    op.create_table(
        "fokontany",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("territory_versions.id"), nullable=False),
        sa.Column("commune_id", sa.Integer(), sa.ForeignKey("communes.id"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("name_normalized", sa.String(length=150), nullable=False),
        sa.CheckConstraint("name <> ''", name="ck_fokontany_name_not_empty"),
        sa.UniqueConstraint(
            "version_id", "commune_id", "code", name="uq_fokontany_version_commune_code"
        ),
        sa.UniqueConstraint(
            "version_id",
            "commune_id",
            "name_normalized",
            name="uq_fokontany_version_commune_name",
        ),
    )
    op.create_index(
        "ix_fokontany_version_commune",
        "fokontany",
        ["version_id", "commune_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fokontany_version_commune", table_name="fokontany")
    op.drop_table("fokontany")
    op.drop_index("ix_communes_version_district", table_name="communes")
    op.drop_table("communes")
    op.drop_index("ix_districts_version_region", table_name="districts")
    op.drop_table("districts")
    op.drop_table("regions")
    op.drop_table("territory_versions")
