from io import BytesIO

import openpyxl

from app.models.actor import Actor
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


def test_signup_requires_geo_and_valid_territory(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    geo = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 47.52, "accuracy_m": 12, "source": "gps"},
    ).json()

    response = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340000001",
            "email": "rakoto@example.com",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": geo["id"],
            "roles": ["orpailleur"],
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "pending"


def test_get_geo_point_rbac(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    geo = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 47.52, "accuracy_m": 12, "source": "gps"},
    ).json()

    actor = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340000009",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": geo["id"],
            "roles": ["orpailleur"],
        },
    ).json()
    actor_row = db_session.query(Actor).filter_by(id=actor["id"]).first()
    actor_row.status = "active"
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "0340000009", "password": "secret"},
    )
    token = login.json()["access_token"]

    ok = client.get(
        f"/api/v1/geo-points/{geo['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 200


def test_signup_rejects_invalid_geo(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    response = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340000002",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": 999,
            "roles": ["orpailleur"],
        },
    )
    assert response.status_code == 400
