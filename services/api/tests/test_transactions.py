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


def test_initiate_transaction_payment(client, db_session):
    from app.models.payment import PaymentProvider

    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session, "seller2@example.com", "0340002000", region.id, district.id, commune.id, version.id
    )
    buyer = _create_actor(
        db_session, "buyer2@example.com", "0340002001", region.id, district.id, commune.id, version.id
    )
    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.commit()

    transaction = client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": None, "quantity": 1, "unit_price": 1000}],
        },
    ).json()

    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/initiate-payment",
        json={"provider_code": "mvola"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "token_manquant"

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": buyer.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    response = client.post(
        f"/api/v1/transactions/{transaction['id']}/initiate-payment",
        headers={"Authorization": f"Bearer {token}"},
        json={"provider_code": "mvola"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_get_transaction_details(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session, "seller3@example.com", "0340003001", region.id, district.id, commune.id, version.id
    )
    buyer = _create_actor(
        db_session, "buyer3@example.com", "0340003002", region.id, district.id, commune.id, version.id
    )

    transaction = client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": None, "quantity": 3, "unit_price": 500}],
        },
    ).json()

    details = client.get(f"/api/v1/transactions/{transaction['id']}")
    assert details.status_code == 200
    payload = details.json()
    assert payload["id"] == transaction["id"]
    assert len(payload["items"]) == 1


def test_list_transactions_filter(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session, "seller4@example.com", "0340004001", region.id, district.id, commune.id, version.id
    )
    buyer = _create_actor(
        db_session, "buyer4@example.com", "0340004002", region.id, district.id, commune.id, version.id
    )
    client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": None, "quantity": 2, "unit_price": 700}],
        },
    )

    response = client.get(f"/api/v1/transactions?seller_actor_id={seller.id}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_transactions_rbac(client, db_session):
    from app.auth.security import hash_password
    from app.models.actor import ActorAuth

    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session, "seller5@example.com", "0340005001", region.id, district.id, commune.id, version.id
    )
    buyer = _create_actor(
        db_session, "buyer5@example.com", "0340005002", region.id, district.id, commune.id, version.id
    )
    other = _create_actor(
        db_session, "other@example.com", "0340005003", region.id, district.id, commune.id, version.id
    )
    db_session.add(ActorAuth(actor_id=other.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    transaction = client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": None, "quantity": 1, "unit_price": 1000}],
        },
    ).json()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": other.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    denied = client.get(
        f"/api/v1/transactions/{transaction['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 400
