from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
from app.models.territory import Commune, District, Region, TerritoryVersion


def _seed_territory(db_session):
    version = TerritoryVersion(
        version_tag="v1",
        source_filename="seed.xlsx",
        checksum_sha256="seed",
        status="active",
        imported_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()
    region = Region(
        version_id=version.id,
        code="01",
        name="Analamanga",
        name_normalized="analamanga",
    )
    db_session.add(region)
    db_session.flush()
    district = District(
        version_id=version.id,
        region_id=region.id,
        code="0101",
        name="Antananarivo Renivohitra",
        name_normalized="antananarivo",
    )
    db_session.add(district)
    db_session.flush()
    commune = Commune(
        version_id=version.id,
        district_id=district.id,
        code="010101",
        name="Antananarivo I",
        name_normalized="antananarivo i",
    )
    db_session.add(commune)
    db_session.commit()
    return region, district, commune, version


def test_export_crud(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Exporter",
        prenoms="Test",
        telephone="0340001300",
        email="export@example.com",
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
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    created = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )
    assert created.status_code == 201

    listed = client.get(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    export_id = listed.json()[0]["id"]
    detail = client.get(
        f"/api/v1/exports/{export_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200
