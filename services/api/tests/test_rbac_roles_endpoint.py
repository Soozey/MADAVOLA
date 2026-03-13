from datetime import datetime, timezone
from io import BytesIO

import openpyxl

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.rbac import RoleCatalog
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.territories.importer import import_territory_excel


def _build_excel() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "region_code",
            "region_name",
            "district_code",
            "district_name",
            "commune_code",
            "commune_name",
            "fokontany_code",
            "fokontany_name",
        ]
    )
    sheet.append(
        [
            "01",
            "Analamanga",
            "0101",
            "Antananarivo Renivohitra",
            "010101",
            "Antananarivo I",
            "010101-001",
            "Isotry",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _create_actor(db_session, role: str, identifier: str):
    version = db_session.query(TerritoryVersion).filter_by(status="active").first()
    region = db_session.query(Region).filter_by(code="01", version_id=version.id).first()
    district = db_session.query(District).filter_by(code="0101", version_id=version.id).first()
    commune = db_session.query(Commune).filter_by(code="010101", version_id=version.id).first()
    actor = Actor(
        type_personne="physique",
        nom=identifier,
        prenoms="Test",
        telephone=f"03477{identifier[-4:]}",
        email=f"{identifier}@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=actor.id, role=role, status="active"))
    db_session.commit()
    return actor


def test_rbac_roles_filter_by_filiere(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    admin = _create_actor(db_session, "admin", "rbacadmin")
    login = client.post("/api/v1/auth/login", json={"identifier": admin.email, "password": "secret"})
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/rbac/roles",
        params={"filiere": "BOIS", "include_common": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert all(row["filiere_scope"] == ["BOIS"] for row in rows)
    assert any(row["code"] == "bois_exploitant" for row in rows)


def test_rbac_roles_for_current_actor_scope(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    actor = _create_actor(db_session, "bois_exploitant", "rbacbois")
    db_session.add(
        RoleCatalog(
            code="bois_exploitant",
            label="Bois Exploitant",
            description="",
            category="BOIS",
            filiere_scope_csv="BOIS",
            is_active=True,
            display_order=1,
        )
    )
    db_session.add(
        RoleCatalog(
            code="pierre_exploitant",
            label="Pierre Exploitant",
            description="",
            category="PIERRE",
            filiere_scope_csv="PIERRE",
            is_active=True,
            display_order=2,
        )
    )
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": actor.email, "password": "secret"})
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/rbac/roles",
        params={"filiere": "BOIS", "for_current_actor": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert [row["code"] for row in rows] == ["bois_exploitant"]


def test_rbac_roles_filter_by_actor_type(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    admin = _create_actor(db_session, "admin", "rbacadmintype")
    login = client.post("/api/v1/auth/login", json={"identifier": admin.email, "password": "secret"})
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/rbac/roles",
        params={"filiere": "OR", "actor_type": "USAGER", "include_common": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert all(row["actor_type"] == "USAGER" for row in rows)
