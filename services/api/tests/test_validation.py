"""
Tests de validation des données d'entrée
"""
from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
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


def test_actor_signup_validation_phone(client, db_session):
    """Test validation téléphone"""
    region, district, commune, fokontany, version = _seed_territory(db_session)

    # Téléphone invalide
    response = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Test",
            "telephone": "123",  # Invalide
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": 1,
            "roles": ["acteur"],
        },
    )
    # La validation se fait au niveau Pydantic ou dans le router
    assert response.status_code in [400, 422]


def test_actor_signup_validation_email(client, db_session):
    """Test validation email"""
    region, district, commune, fokontany, version = _seed_territory(db_session)

    # Email invalide
    response = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Test",
            "telephone": "0340000001",
            "email": "invalid-email",  # Invalide
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": 1,
            "roles": ["acteur"],
        },
    )
    assert response.status_code in [400, 422]


def test_lot_validation_quantity(client, db_session):
    """Test validation quantité lot"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Test",
        telephone="0340000002",
        email="test@example.com",
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
        json={"identifier": "test@example.com", "password": "secret"},
    )
    token = login.json()["access_token"]

    # Quantité négative
    response = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filiere": "OR",
            "product_type": "poudre",
            "unit": "g",
            "quantity": -10,  # Invalide
            "declare_geo_point_id": 1,
            "declared_by_actor_id": actor.id,
        },
    )
    assert response.status_code in [400, 422]


def test_geo_validation_coordinates(client, db_session):
    """Test validation coordonnées GPS"""
    # Latitude invalide
    response = client.post(
        "/api/v1/geo-points",
        json={"lat": 100, "lon": 47.52, "accuracy_m": 12},  # lat > 90
    )
    assert response.status_code in [400, 422]

    # Longitude invalide
    response = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 200, "accuracy_m": 12},  # lon > 180
    )
    assert response.status_code in [400, 422]
