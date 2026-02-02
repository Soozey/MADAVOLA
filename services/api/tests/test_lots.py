from datetime import datetime, timezone
from io import BytesIO

import openpyxl

from app.models.actor import Actor, ActorAuth
from app.models.geo import GeoPoint
from app.models.payment import PaymentProvider, PaymentRequest
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.auth.security import hash_password


def _build_excel() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "region_code",
            "region_name",
            "district_code",
            "district_name",
            "commune_code",
            "commune_name",
            "fokontany_code",
            "fokontany_name",
        ]
    )
    sheet.append(
        [
            "01",
            "Analamanga",
            "0101",
            "Antananarivo Renivohitra",
            "010101",
            "Antananarivo I",
            "010101-001",
            "Isotry",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


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


def test_lot_create_and_transfer(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = Actor(
        type_personne="physique",
        nom="Seller",
        prenoms="Lot",
        telephone="0340008001",
        email="sellerlot@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    buyer = Actor(
        type_personne="physique",
        nom="Buyer",
        prenoms="Lot",
        telephone="0340008002",
        email="buyerlot@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([seller, buyer])
    db_session.flush()
    db_session.add(ActorAuth(actor_id=seller.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12)
    db_session.add(geo)
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": seller.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filiere": "OR",
            "product_type": "or_brut",
            "unit": "g",
            "quantity": 10,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": seller.id,
        },
    ).json()

    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.flush()
    payment_request = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=buyer.id,
        payee_actor_id=seller.id,
        amount=10000,
        currency="MGA",
        status="success",
        external_ref="lot-pay-1",
    )
    db_session.add(payment_request)
    db_session.commit()

    transfer = client.post(
        f"/api/v1/lots/{lot['id']}/transfer",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_owner_actor_id": buyer.id, "payment_request_id": payment_request.id},
    )
    assert transfer.status_code == 200
