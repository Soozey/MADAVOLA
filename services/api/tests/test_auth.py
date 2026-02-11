from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole, RefreshToken
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion


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
    db_session.flush()
    fokontany = Fokontany(
        version_id=version.id,
        commune_id=commune.id,
        code="010101-001",
        name="Isotry",
        name_normalized="isotry",
    )
    db_session.add(fokontany)
    db_session.commit()
    return region, district, commune, fokontany, version


def _create_actor(
    db_session,
    region=None,
    district=None,
    commune=None,
    fokontany=None,
    version=None,
    status="active",
):
    if not all([region, district, commune, fokontany, version]):
        region, district, commune, fokontany, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone="0340000000",
        email="test@example.com",
        status=status,
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        fokontany_id=fokontany.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(
        ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1)
    )
    db_session.commit()
    return actor


def test_login_and_me(client, db_session):
    region, district, commune, fokontany, version = _seed_territory(db_session)
    actor = _create_actor(db_session, region, district, commune, fokontany, version)
    
    # Add a role
    db_session.add(
        ActorRole(
            actor_id=actor.id,
            role="acteur",
            status="active",
            valid_from=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.com", "password": "secret"},
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    data = me.json()
    assert data["id"] == actor.id
    assert data["nom"] == "Test"
    assert data["prenoms"] == "User"
    
    # Check territory info
    assert data["region"] is not None
    assert data["region"]["code"] == "01"
    assert data["region"]["name"] == "Analamanga"
    assert data["district"] is not None
    assert data["district"]["code"] == "0101"
    assert data["commune"] is not None
    assert data["commune"]["code"] == "010101"
    assert data["fokontany"] is not None
    assert data["fokontany"]["code"] == "010101-001"
    
    # Check roles
    assert "roles" in data
    assert len(data["roles"]) == 1
    assert data["roles"][0]["role"] == "acteur"
    assert data["roles"][0]["status"] == "active"


def test_refresh_and_logout(client, db_session):
    _create_actor(db_session)
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.com", "password": "secret"},
    )
    tokens = response.json()

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert logout.status_code == 200

    stored = db_session.query(RefreshToken).filter_by(actor_id=1).all()
    assert any(t.revoked_at is not None for t in stored)
