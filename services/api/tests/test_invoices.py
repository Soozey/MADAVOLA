from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
from app.models.invoice import Invoice
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


def test_get_invoice_rbac(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = Actor(
        type_personne="physique",
        nom="Seller",
        prenoms="Inv",
        telephone="0340000400",
        email="sellerinv@example.com",
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
        prenoms="Inv",
        telephone="0340000401",
        email="buyerinv@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    other = Actor(
        type_personne="physique",
        nom="Other",
        prenoms="Inv",
        telephone="0340000402",
        email="otherinv@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([seller, buyer, other])
    db_session.flush()
    db_session.add(ActorAuth(actor_id=other.id, password_hash=hash_password("secret"), is_active=1))
    invoice = Invoice(
        invoice_number="INV-00000001",
        transaction_id=1,
        seller_actor_id=seller.id,
        buyer_actor_id=buyer.id,
        total_amount=1000,
        status="issued",
    )
    db_session.add(invoice)
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": other.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    denied = client.get(
        f"/api/v1/invoices/{invoice.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 400
