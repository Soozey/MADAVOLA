from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
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


def test_ledger_list_and_balance(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Ledger",
        prenoms="Test",
        telephone="0340009001",
        email="ledger@example.com",
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
    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12)
    db_session.add(geo)
    db_session.flush()
    lot = Lot(
        filiere="OR",
        product_type="or_brut",
        unit="g",
        quantity=10,
        declared_by_actor_id=actor.id,
        current_owner_actor_id=actor.id,
        status="available",
        declare_geo_point_id=geo.id,
    )
    db_session.add(lot)
    db_session.flush()
    db_session.add(
        InventoryLedger(
            actor_id=actor.id,
            lot_id=lot.id,
            movement_type="create",
            quantity_delta=10,
            ref_event_type="lot",
            ref_event_id=str(lot.id),
        )
    )
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    entries = client.get(
        "/api/v1/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert entries.status_code == 200
    assert len(entries.json()) >= 1

    balance = client.get(
        "/api/v1/ledger/balance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert balance.status_code == 200
    assert balance.json()[0]["quantity"] == 10.0
