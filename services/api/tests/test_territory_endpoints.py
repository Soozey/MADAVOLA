from io import BytesIO

import openpyxl

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
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


def test_cascade_endpoints(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    regions = client.get("/api/v1/territories/regions").json()
    assert len(regions) == 1
    assert regions[0]["code"] == "01"
    assert regions[0]["name"] == "Analamanga"

    districts = client.get("/api/v1/territories/districts?region_code=01").json()
    assert len(districts) == 1
    assert districts[0]["code"] == "0101"
    assert districts[0]["name"] == "Antananarivo Renivohitra"
    assert districts[0]["region_code"] == "01"

    communes = client.get("/api/v1/territories/communes?district_code=0101").json()
    assert len(communes) == 1
    assert communes[0]["code"] == "010101"
    assert communes[0]["name"] == "Antananarivo I"
    assert communes[0]["district_code"] == "0101"
    assert communes[0]["commune_mobile_money_msisdn"] is None

    all_communes = client.get("/api/v1/territories/communes-all").json()
    assert len(all_communes) == 1
    assert all_communes[0]["code"] == "010101"
    assert all_communes[0]["district_code"] == "0101"
    assert all_communes[0]["region_code"] == "01"

    fokontany = client.get("/api/v1/territories/fokontany?commune_code=010101").json()
    assert len(fokontany) == 1
    assert fokontany[0]["code"] == "010101-001"
    assert fokontany[0]["name"] == "Isotry"
    assert fokontany[0]["commune_code"] == "010101"

    active = client.get("/api/v1/territories/active").json()
    assert active["version_tag"] == "v1"

    version = client.get("/api/v1/territories/versions/v1").json()
    assert version["version_tag"] == "v1"


def test_import_endpoint_requires_admin_role(client, db_session):
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
    sheet.append(["02", "Itasy", "0201", "Miarinarivo", "020101", "Miarinarivo", "020101-001", "Centre"])
    buffer = BytesIO()
    workbook.save(buffer)
    payload = buffer.getvalue()

    forbidden = client.post(
        "/api/v1/territories/import?version_tag=v-auth-1",
        files={"file": ("territory.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["detail"]["message"] in {"token_manquant", "role_insuffisant"}

    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v-base")
    from app.models.territory import Commune, District, Region, TerritoryVersion

    version = db_session.query(TerritoryVersion).filter_by(version_tag="v-base").first()
    region = db_session.query(Region).filter_by(version_id=version.id, code="01").first()
    district = db_session.query(District).filter_by(version_id=version.id, code="0101").first()
    commune = db_session.query(Commune).filter_by(version_id=version.id, code="010101").first()
    admin = Actor(
        type_personne="physique",
        nom="Admin",
        prenoms="Root",
        telephone="0349000000",
        email="admin.territory@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
    )
    db_session.add(admin)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=admin.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=admin.id, role="admin", status="active"))
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": admin.email, "password": "secret"})
    token = login.json()["access_token"]
    allowed = client.post(
        "/api/v1/territories/import?version_tag=v-auth-2",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("territory.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert allowed.status_code == 200
    assert allowed.json()["version_tag"] == "v-auth-2"
