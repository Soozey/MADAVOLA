from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.territory import Commune, District, Region, TerritoryVersion


def _create_admin(db_session):
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
    db_session.flush()

    actor = Actor(
        type_personne="physique",
        nom="Admin",
        prenoms="Root",
        telephone="0349999999",
        email="admin@example.com",
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
    db_session.add(ActorRole(actor_id=actor.id, role="admin", status="active"))
    db_session.commit()
    return actor


def test_payment_provider_crud(client, db_session):
    admin = _create_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    create = client.post(
        "/api/v1/payment-providers",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "mvola", "name": "mVola", "enabled": False},
    )
    assert create.status_code == 201

    listed = client.get(
        "/api/v1/payment-providers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["code"] == "mvola"

    provider_id = create.json()["id"]
    update = client.patch(
        f"/api/v1/payment-providers/{provider_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": True},
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is True
