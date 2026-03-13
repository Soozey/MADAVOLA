"""rbac role catalog metadata

Revision ID: 0021_rbac_role_catalog
Revises: 0020_regime_or_extensions
Create Date: 2026-02-23 07:05:00.000000
"""

from collections.abc import Iterable

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0021_rbac_role_catalog"
down_revision = "0020_regime_or_extensions"
branch_labels = None
depends_on = None


def _infer_filiere_scope(role_code: str) -> str:
    if role_code.startswith("pierre_"):
        return "PIERRE"
    if role_code.startswith("bois_"):
        return "BOIS"
    if role_code in {
        "orpailleur",
        "collecteur",
        "comptoir_operator",
        "comptoir_compliance",
        "comptoir_director",
        "com",
        "com_admin",
        "com_agent",
        "gue",
        "gue_or_agent",
        "douanes_agent",
        "raffinerie_agent",
        "lab_bgglm",
        "mines_region_agent",
        "bijoutier",
    }:
        return "OR"
    return "OR,PIERRE,BOIS"


def _infer_category(role_code: str) -> str:
    if role_code.startswith("bois_"):
        return "BOIS"
    if role_code.startswith("pierre_"):
        return "PIERRE"
    if role_code in {"orpailleur", "collecteur", "bijoutier", "acteur"}:
        return "Acteurs terrain"
    if role_code in {"police", "gendarmerie", "controleur", "douanes_agent", "dgd", "mines_region_agent"}:
        return "Controle"
    if role_code in {"commune", "commune_agent", "fokontany", "region", "region_agent", "district_agent"}:
        return "Territorial"
    if role_code in {"com", "com_admin", "com_agent", "gue", "gue_or_agent", "comptoir_operator", "comptoir_compliance", "comptoir_director"}:
        return "Export et regulation"
    return "Administration"


def _title(code: str) -> str:
    return " ".join(x.capitalize() for x in code.split("_") if x)


def _seed_rows() -> Iterable[dict]:
    from app.auth.roles_config import ROLE_DEFINITIONS

    rows = []
    for idx, (code, defn) in enumerate(sorted(ROLE_DEFINITIONS.items()), start=1):
        rows.append(
            {
                "code": code,
                "label": _title(code),
                "description": defn.get("description", ""),
                "category": _infer_category(code),
                "filiere_scope_csv": _infer_filiere_scope(code),
                "tags_csv": None,
                "is_active": True,
                "display_order": idx,
            }
        )
    return rows


def upgrade() -> None:
    op.create_table(
        "rbac_role_catalog",
        sa.Column("code", sa.String(length=50), primary_key=True, nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="Autres"),
        sa.Column("filiere_scope_csv", sa.String(length=120), nullable=False, server_default="OR,PIERRE,BOIS"),
        sa.Column("tags_csv", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    role_catalog = sa.table(
        "rbac_role_catalog",
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("filiere_scope_csv", sa.String),
        sa.column("tags_csv", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("display_order", sa.Integer),
    )
    op.bulk_insert(role_catalog, list(_seed_rows()))


def downgrade() -> None:
    op.drop_table("rbac_role_catalog")

