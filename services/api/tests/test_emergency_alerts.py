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


def _create_actor(db_session, region, district, commune, version, email: str, role_name: str):
    suffix = "".join(ch for ch in email if ch.isdigit())[-7:]
    if not suffix:
        suffix = str(sum(ord(ch) for ch in email) % 10_000_000).rjust(7, "0")
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone=f"034{suffix}",
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


def _token(client, actor_email: str) -> str:
    login = client.post("/api/v1/auth/login", json={"identifier": actor_email, "password": "secret"})
    return login.json()["access_token"]


def test_emergency_alert_create_list_update(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    sender = _create_actor(db_session, region, district, commune, version, "sender@example.com", "acteur")
    police = _create_actor(db_session, region, district, commune, version, "police@example.com", "police")

    sender_token = _token(client, sender.email)
    police_token = _token(client, police.email)

    created = client.post(
        "/api/v1/emergency-alerts",
        headers={"Authorization": f"Bearer {sender_token}"},
        json={
            "title": "Alerte test",
            "message": "Incident securite",
            "severity": "high",
            "target_service": "police",
            "filiere": "BOIS",
        },
    )
    assert created.status_code == 201
    alert_id = created.json()["id"]
    assert created.json()["status"] == "open"

    mine = client.get("/api/v1/emergency-alerts", headers={"Authorization": f"Bearer {sender_token}"})
    assert mine.status_code == 200
    assert len(mine.json()) == 1

    managed = client.patch(
        f"/api/v1/emergency-alerts/{alert_id}/status",
        headers={"Authorization": f"Bearer {police_token}"},
        json={"status": "acknowledged"},
    )
    assert managed.status_code == 200
    assert managed.json()["status"] == "acknowledged"
