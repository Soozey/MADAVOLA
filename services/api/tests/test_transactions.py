from datetime import datetime, timezone

from app.models.actor import Actor
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


def _create_actor(db_session, email: str, phone: str, region_id, district_id, commune_id, version_id):
    actor = Actor(
        type_personne="physique",
        nom=email.split("@")[0],
        prenoms="Test",
        telephone=phone,
        email=email,
        status="active",
        region_id=region_id,
        district_id=district_id,
        commune_id=commune_id,
        territory_version_id=version_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.commit()
    return actor


def test_create_transaction(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session, "seller@example.com", "0340001000", region.id, district.id, commune.id, version.id
    )
    buyer = _create_actor(
        db_session, "buyer@example.com", "0340001001", region.id, district.id, commune.id, version.id
    )

    response = client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [
                {"lot_id": None, "quantity": 2, "unit_price": 1000},
                {"lot_id": None, "quantity": 1, "unit_price": 500},
            ],
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["total_amount"] == 2500.0
