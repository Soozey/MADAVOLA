from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
from app.models.fee import Fee
from app.models.geo import GeoPoint
from app.models.payment import PaymentProvider
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
        mobile_money_msisdn="0340000000",
    )
    db_session.add(commune)
    db_session.commit()
    return region, district, commune, version


def test_orpailleur_signup_creates_opening_fee(client, db_session):
    _seed_territory(db_session)
    geo = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 47.52, "accuracy_m": 12, "source": "gps"},
    ).json()
    created = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340011001",
            "email": "rakoto.fee@example.com",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "geo_point_id": geo["id"],
            "roles": ["orpailleur"],
        },
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["opening_fee_status"] == "pending"
    assert payload["opening_fee_id"] is not None
    fee = db_session.query(Fee).filter_by(id=payload["opening_fee_id"]).first()
    assert fee is not None
    assert float(fee.amount) == 10000.0


def test_initiate_fee_payment_uses_commune_beneficiary(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Fee",
        prenoms="User",
        telephone="0340011002",
        email="fee.user@example.com",
        status="pending",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    fee = Fee(
        fee_type="account_opening_commune",
        actor_id=actor.id,
        commune_id=commune.id,
        amount=10000,
        currency="MGA",
        status="pending",
    )
    db_session.add(fee)
    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.commit()

    response = client.post(
        f"/api/v1/fees/{fee.id}/initiate-payment",
        json={"provider_code": "mvola", "external_ref": "fee-ext-1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["beneficiary_msisdn"] == "0340000000"


def test_verify_lot_endpoint(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Lot",
        prenoms="Owner",
        telephone="0340011003",
        email="lot.owner@example.com",
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
    login = client.post("/api/v1/auth/login", json={"identifier": actor.email, "password": "secret"})
    token = login.json()["access_token"]
    geo = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 47.52, "accuracy_m": 12, "source": "gps"},
    ).json()
    lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filiere": "OR",
            "product_type": "or_brut",
            "unit": "g",
            "quantity": 10,
            "declare_geo_point_id": geo["id"],
            "declared_by_actor_id": actor.id,
            "notes": "test",
            "photo_urls": [],
        },
    ).json()
    verify = client.get(f"/api/v1/verify/lot/{lot['id']}")
    assert verify.status_code == 200
    assert verify.json()["id"] == lot["id"]
