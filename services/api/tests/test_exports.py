from datetime import datetime, timezone, date
import hashlib
import re

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.models.export import ExportDossier


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
    local_part = email.split("@")[0]
    digits = re.sub(r"\D", "", local_part)[-4:]
    if not digits:
        digits = f"{int(hashlib.sha1(local_part.encode('utf-8')).hexdigest(), 16) % 10000:04d}"
    phone_suffix = digits.rjust(4, "0")
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone=f"034000{phone_suffix}",
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


def test_export_crud(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "export@example.com", "acteur")

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


def test_export_filters(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "export@example.com", "acteur")

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    # Create multiple exports with different statuses
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )
    export2 = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "Paris", "total_weight": 8.0},
    )
    export2_id = export2.json()["id"]

    # Update status
    client.patch(
        f"/api/v1/exports/{export2_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "submitted"},
    )

    # Filter by status
    filtered = client.get(
        "/api/v1/exports?status=submitted",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["status"] == "submitted"

    # Filter by date
    today = date.today()
    filtered_date = client.get(
        f"/api/v1/exports?date_from={today}&date_to={today}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filtered_date.status_code == 200
    assert len(filtered_date.json()) >= 2


def test_export_rbac_admin_sees_all(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    admin = _create_actor_with_role(db_session, region, district, commune, version, "admin@example.com", "admin")
    actor1 = _create_actor_with_role(db_session, region, district, commune, version, "actor1@example.com", "acteur")
    actor2 = _create_actor_with_role(db_session, region, district, commune, version, "actor2@example.com", "acteur")

    # Actor1 creates export
    login1 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor1.email, "password": "secret"},
    )
    token1 = login1.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token1}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )

    # Actor2 creates export
    login2 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor2.email, "password": "secret"},
    )
    token2 = login2.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token2}"},
        json={"destination": "Paris", "total_weight": 8.0},
    )

    # Admin sees all
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    admin_token = admin_login.json()["access_token"]
    all_exports = client.get(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert all_exports.status_code == 200
    assert len(all_exports.json()) == 2


def test_export_rbac_commune_agent_sees_commune_only(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    # Create second commune
    commune2 = Commune(
        version_id=version.id,
        district_id=district.id,
        code="010102",
        name="Antananarivo II",
        name_normalized="antananarivo ii",
    )
    db_session.add(commune2)
    db_session.commit()

    agent = _create_actor_with_role(
        db_session, region, district, commune, version, "agent@example.com", "commune_agent"
    )
    actor1 = _create_actor_with_role(db_session, region, district, commune, version, "actor1@example.com", "acteur")
    actor2 = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone="0340001301",
        email="actor2@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune2.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor2)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor2.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(
        ActorRole(
            actor_id=actor2.id,
            role="acteur",
            status="active",
            valid_from=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    # Actor1 (same commune) creates export
    login1 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor1.email, "password": "secret"},
    )
    token1 = login1.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token1}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )

    # Actor2 (different commune) creates export
    login2 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor2.email, "password": "secret"},
    )
    token2 = login2.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token2}"},
        json={"destination": "Paris", "total_weight": 8.0},
    )

    # Agent sees only same commune
    agent_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": agent.email, "password": "secret"},
    )
    agent_token = agent_login.json()["access_token"]
    agent_exports = client.get(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert agent_exports.status_code == 200
    assert len(agent_exports.json()) == 1
    assert agent_exports.json()[0]["destination"] == "Dubai"


def test_export_rbac_actor_sees_own_only(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor1 = _create_actor_with_role(db_session, region, district, commune, version, "actor1@example.com", "acteur")
    actor2 = _create_actor_with_role(db_session, region, district, commune, version, "actor2@example.com", "acteur")

    # Actor1 creates export
    login1 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor1.email, "password": "secret"},
    )
    token1 = login1.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token1}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )

    # Actor2 creates export
    login2 = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor2.email, "password": "secret"},
    )
    token2 = login2.json()["access_token"]
    client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token2}"},
        json={"destination": "Paris", "total_weight": 8.0},
    )

    # Actor1 sees only own
    exports1 = client.get(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert exports1.status_code == 200
    assert len(exports1.json()) == 1
    assert exports1.json()[0]["destination"] == "Dubai"


def test_export_status_update_rbac(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    admin = _create_actor_with_role(db_session, region, district, commune, version, "admin@example.com", "admin")
    actor = _create_actor_with_role(db_session, region, district, commune, version, "actor@example.com", "acteur")

    # Actor creates export
    login_actor = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token_actor = login_actor.json()["access_token"]
    created = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token_actor}"},
        json={"destination": "Dubai", "total_weight": 12.5},
    )
    export_id = created.json()["id"]

    # Actor can update to submitted
    updated = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_actor}"},
        json={"status": "submitted"},
    )
    assert updated.status_code == 200

    # Actor cannot approve (needs admin/dirigeant)
    failed = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_actor}"},
        json={"status": "approved"},
    )
    assert failed.status_code == 400

    # Admin can approve
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token_admin = login_admin.json()["access_token"]
    approved = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
