from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.admin import SystemConfig
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


def _create_actor_with_role(db_session, region, district, commune, version, email, role_name=None):
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone="0340001300",
        email=email,
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
    if role_name:
        db_session.add(
            ActorRole(
                actor_id=actor.id,
                role=role_name,
                status="active",
                valid_from=datetime.now(timezone.utc),
            )
        )
    db_session.commit()
    return actor


def test_system_config_crud(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    admin = _create_actor_with_role(db_session, region, district, commune, version, "admin@example.com", "admin")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    # Create config
    created = client.post(
        "/api/v1/admin/config",
        headers={"Authorization": f"Bearer {token}"},
        json={"key": "app.name", "value": "MADAVOLA", "description": "Application name"},
    )
    assert created.status_code == 201
    assert created.json()["key"] == "app.name"
    assert created.json()["value"] == "MADAVOLA"

    config_id = created.json()["id"]

    # List configs
    listed = client.get(
        "/api/v1/admin/config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    # Get config
    detail = client.get(
        f"/api/v1/admin/config/{config_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail.status_code == 200
    assert detail.json()["key"] == "app.name"

    # Update config
    updated = client.patch(
        f"/api/v1/admin/config/{config_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": "MADAVOLA v2"},
    )
    assert updated.status_code == 200
    assert updated.json()["value"] == "MADAVOLA v2"

    # Delete config
    deleted = client.delete(
        f"/api/v1/admin/config/{config_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 204


def test_system_config_rbac_non_admin_forbidden(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "actor@example.com", "acteur")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    # Non-admin cannot create config
    failed = client.post(
        "/api/v1/admin/config",
        headers={"Authorization": f"Bearer {token}"},
        json={"key": "app.name", "value": "MADAVOLA"},
    )
    assert failed.status_code == 400


def test_admin_assign_role(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    admin = _create_actor_with_role(db_session, region, district, commune, version, "admin@example.com", "admin")
    actor = _create_actor_with_role(db_session, region, district, commune, version, "actor@example.com", "acteur")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    # Assign role
    assigned = client.post(
        f"/api/v1/admin/actors/{actor.id}/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"actor_id": actor.id, "role": "commune_agent"},
    )
    assert assigned.status_code == 201
    assert assigned.json()["role"] == "commune_agent"
    assert assigned.json()["status"] == "active"

    # List roles
    roles = client.get(
        f"/api/v1/admin/actors/{actor.id}/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert roles.status_code == 200
    assert len(roles.json()) == 2  # acteur + commune_agent

    role_id = assigned.json()["id"]

    # Update role
    updated = client.patch(
        f"/api/v1/admin/roles/{role_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "inactive"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "inactive"

    # Revoke role
    revoked = client.delete(
        f"/api/v1/admin/roles/{role_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoked.status_code == 204


def test_admin_role_rbac_non_admin_forbidden(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor1 = _create_actor_with_role(db_session, region, district, commune, version, "actor1@example.com", "acteur")
    actor2 = _create_actor_with_role(db_session, region, district, commune, version, "actor2@example.com", "acteur")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor1.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    # Non-admin cannot assign role
    failed = client.post(
        f"/api/v1/admin/actors/{actor2.id}/roles",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "commune_agent"},
    )
    assert failed.status_code == 400
