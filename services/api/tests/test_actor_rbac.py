from datetime import datetime, timezone
from io import BytesIO

import openpyxl

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
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
    sheet.append(
        [
            "01",
            "Analamanga",
            "0101",
            "Antananarivo Renivohitra",
            "010102",
            "Antananarivo II",
            "010102-001",
            "Ankadifotsy",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _create_actor(db_session, commune_code: str, role: str, identifier: str):
    version = db_session.query(TerritoryVersion).filter_by(status="active").first()
    region = db_session.query(Region).filter_by(code="01", version_id=version.id).first()
    district = db_session.query(District).filter_by(code="0101", version_id=version.id).first()
    commune = (
        db_session.query(Commune)
        .filter_by(code=commune_code, version_id=version.id)
        .first()
    )
    actor = Actor(
        type_personne="physique",
        nom=identifier,
        prenoms="Test",
        telephone=f"0340000{identifier}",
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


def test_commune_agent_scope(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    commune_agent = _create_actor(db_session, "010101", "commune_agent", "agent1")
    _create_actor(db_session, "010101", "orpailleur", "orp1")
    _create_actor(db_session, "010102", "orpailleur", "orp2")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": commune_agent.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/actors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    results = response.json()
    assert all(r["commune_code"] == "010101" for r in results)


def test_get_actor_rbac(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    actor = _create_actor(db_session, "010101", "orpailleur", "orp3")
    other = _create_actor(db_session, "010101", "orpailleur", "orp4")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": other.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    denied = client.get(
        f"/api/v1/actors/{actor.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 400
