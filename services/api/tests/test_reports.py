from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.lot import InventoryLedger
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.models.transaction import TradeTransaction


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


def test_report_commune(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    agent = Actor(
        type_personne="physique",
        nom="Commune",
        prenoms="Agent",
        telephone="0340001400",
        email="agent@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(agent)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=agent.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=agent.id, role="commune_agent", status="active"))
    db_session.add(
        InventoryLedger(
            actor_id=agent.id,
            lot_id=1,
            movement_type="create",
            quantity_delta=5,
            ref_event_type="lot",
            ref_event_id="1",
        )
    )
    db_session.add(
        TradeTransaction(
            seller_actor_id=agent.id,
            buyer_actor_id=agent.id,
            status="paid",
            total_amount=1000,
            currency="MGA",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": agent.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    response = client.get(
        f"/api/v1/reports/commune?commune_id={commune.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_report_national_requires_admin(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    user = Actor(
        type_personne="physique",
        nom="User",
        prenoms="Test",
        telephone="0340001500",
        email="user@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=user.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    denied = client.get(
        "/api/v1/reports/national",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 400
