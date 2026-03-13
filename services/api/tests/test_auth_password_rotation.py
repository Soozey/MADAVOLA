from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
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
    region = Region(version_id=version.id, code="01", name="Analamanga", name_normalized="analamanga")
    db_session.add(region)
    db_session.flush()
    district = District(
        version_id=version.id,
        region_id=region.id,
        code="0101",
        name="Antananarivo Renivohitra",
        name_normalized="antananarivo renivohitra",
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


def test_password_change_required_blocks_api_until_rotation(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Admin",
        prenoms="Demo",
        telephone="0340000999",
        email="admin.rotation@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(
        ActorAuth(
            actor_id=actor.id,
            password_hash=hash_password("admin123"),
            is_active=1,
            must_change_password=1,
        )
    )
    db_session.add(
        ActorRole(
            actor_id=actor.id,
            role="admin",
            status="active",
            valid_from=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin.rotation@example.com", "password": "admin123"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["must_change_password"] is True
    token = payload["access_token"]

    blocked = client.get(
        "/api/v1/actors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["message"] == "password_change_required"

    changed = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "admin123", "new_password": "nouveau-pass-123"},
    )
    assert changed.status_code == 200

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["must_change_password"] is False

    allowed = client.get(
        "/api/v1/actors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert allowed.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin.rotation@example.com", "password": "admin123"},
    )
    assert old_login.status_code == 400

    new_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin.rotation@example.com", "password": "nouveau-pass-123"},
    )
    assert new_login.status_code == 200
    assert new_login.json()["must_change_password"] is False
