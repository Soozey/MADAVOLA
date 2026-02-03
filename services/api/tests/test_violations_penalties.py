from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.penalty import Inspection, ViolationCase
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


def test_violation_and_penalty(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    inspector = Actor(
        type_personne="physique",
        nom="Inspect",
        prenoms="Two",
        telephone="0340001200",
        email="inspect2@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(inspector)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=inspector.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=inspector.id, role="controleur", status="active"))
    inspection = Inspection(
        inspector_actor_id=inspector.id,
        result="infraction",
    )
    db_session.add(inspection)
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": inspector.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    violation = client.post(
        "/api/v1/violations",
        headers={"Authorization": f"Bearer {token}"},
        json={"inspection_id": inspection.id, "violation_type": "fraude"},
    )
    assert violation.status_code == 201

    penalty = client.post(
        "/api/v1/penalties",
        headers={"Authorization": f"Bearer {token}"},
        json={"violation_case_id": violation.json()["id"], "penalty_type": "fine", "amount": 5000},
    )
    assert penalty.status_code == 201
