from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.lot import Lot
from app.models.territory import Commune, District, Region, TerritoryVersion


def _seed_territory(db_session):
    version = TerritoryVersion(
        version_tag="v-msg-mkt",
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


def _create_actor(db_session, *, email: str, phone: str, role: str, region_id: int, district_id: int, commune_id: int, version_id: int):
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
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=actor.id, role=role, status="active"))
    db_session.commit()
    return actor


def _auth(client, identifier: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": "secret"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_contact_request_and_direct_messages_flow(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor_a = _create_actor(
        db_session,
        email="a@test.mg",
        phone="0348111111",
        role="orpailleur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    actor_b = _create_actor(
        db_session,
        email="b@test.mg",
        phone="0348222222",
        role="collecteur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    actor_c = _create_actor(
        db_session,
        email="c@test.mg",
        phone="0348333333",
        role="collecteur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    headers_a = _auth(client, actor_a.email)
    headers_b = _auth(client, actor_b.email)

    request_resp = client.post("/api/v1/messages/contacts", headers=headers_a, json={"target_actor_id": actor_b.id})
    assert request_resp.status_code == 201
    contact_id = request_resp.json()["id"]

    decision_resp = client.post(
        f"/api/v1/messages/contacts/{contact_id}/decision",
        headers=headers_b,
        json={"decision": "accepted"},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["status"] == "accepted"

    send_resp = client.post(
        "/api/v1/messages",
        headers=headers_a,
        json={"receiver_actor_id": actor_b.id, "body": "Bonjour collecteur"},
    )
    assert send_resp.status_code == 201
    assert send_resp.json()["body"] == "Bonjour collecteur"

    convo = client.get(f"/api/v1/messages?with_actor_id={actor_a.id}", headers=headers_b)
    assert convo.status_code == 200
    assert len(convo.json()) >= 1

    no_contact_send = client.post(
        "/api/v1/messages",
        headers=headers_a,
        json={"receiver_actor_id": actor_c.id, "body": "No contact"},
    )
    assert no_contact_send.status_code == 400


def test_marketplace_offer_create_filter_close(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        email="seller@test.mg",
        phone="0348444444",
        role="orpailleur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    buyer = _create_actor(
        db_session,
        email="buyer@test.mg",
        phone="0348555555",
        role="collecteur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    geo = GeoPoint(lat=-18.8792, lon=47.5079, accuracy_m=10, source="test", actor_id=seller.id)
    db_session.add(geo)
    db_session.flush()
    lot = Lot(
        filiere="OR",
        product_type="or_brut",
        unit="g",
        quantity=120.0,
        declared_by_actor_id=seller.id,
        current_owner_actor_id=seller.id,
        status="available",
        declare_geo_point_id=geo.id,
    )
    db_session.add(lot)
    db_session.commit()

    seller_headers = _auth(client, seller.email)
    buyer_headers = _auth(client, buyer.email)

    create_offer = client.post(
        "/api/v1/marketplace/offers",
        headers=seller_headers,
        json={
            "offer_type": "sell",
            "filiere": "OR",
            "lot_id": lot.id,
            "product_type": "or_brut",
            "quantity": 30,
            "unit": "g",
            "unit_price": 5000,
            "currency": "MGA",
        },
    )
    assert create_offer.status_code == 201
    offer_id = create_offer.json()["id"]

    offer_list = client.get("/api/v1/marketplace/offers?offer_type=sell&min_price=1000&max_price=6000", headers=buyer_headers)
    assert offer_list.status_code == 200
    assert any(row["id"] == offer_id for row in offer_list.json())

    close_resp = client.post(f"/api/v1/marketplace/offers/{offer_id}/close", headers=seller_headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    cannot_close = client.post(f"/api/v1/marketplace/offers/{offer_id}/close", headers=buyer_headers)
    assert cannot_close.status_code == 400
