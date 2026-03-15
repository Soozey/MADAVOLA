from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.lot import Lot
from app.models.or_compliance import CollectorCard, KaraBolamenaCard
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.models.transaction import TradeTransaction, TradeTransactionItem


def _seed_territory(db_session):
    version = TerritoryVersion(
        version_tag="v-trade-or",
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
    district = District(version_id=version.id, region_id=region.id, code="0101", name="District", name_normalized="district")
    db_session.add(district)
    db_session.flush()
    commune = Commune(version_id=version.id, district_id=district.id, code="010101", name="Commune", name_normalized="commune")
    db_session.add(commune)
    db_session.commit()
    return region, district, commune, version


def _create_actor(
    db_session,
    *,
    role: str,
    email: str,
    phone: str,
    region_id: int,
    district_id: int,
    commune_id: int,
    version_id: int,
    type_personne: str = "physique",
):
    actor = Actor(
        type_personne=type_personne,
        nom=role,
        prenoms="Trade",
        telephone=phone,
        email=email,
        status="active",
        cin="CIN-OR-1",
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


def _auth(client, identifier: str, password: str = "secret") -> dict:
    resp = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_or_lot(db_session, *, owner_id: int, geo_id: int):
    lot = Lot(
        filiere="OR",
        product_type="or_brut",
        unit="g",
        quantity=10,
        declared_by_actor_id=owner_id,
        current_owner_actor_id=owner_id,
        status="available",
        declare_geo_point_id=geo_id,
        photo_urls_json="[]",
        qr_code=f"QR-{owner_id}-{geo_id}",
        lot_number=f"LOT-{owner_id}-{geo_id}",
        traceability_id=f"TRACE-{owner_id}-{geo_id}",
    )
    db_session.add(lot)
    db_session.commit()
    return lot


def test_trades_or_chain_blocks_orpailleur_direct_to_comptoir(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        role="orpailleur",
        email="orpailleur-trade@test.mg",
        phone="0342000001",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    buyer = _create_actor(
        db_session,
        role="comptoir_operator",
        email="comptoir-trade@test.mg",
        phone="0342000002",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    db_session.add(
        KaraBolamenaCard(
            actor_id=seller.id,
            commune_id=commune.id,
            unique_identifier=f"KARA-{seller.id}",
            status="active",
            cin="CIN-OR-1",
            nationality="mg",
            residence_verified=True,
            tax_compliant=True,
            zone_allowed=True,
            public_order_clear=True,
            issued_at=datetime.now(timezone.utc),
            validated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=120),
        )
    )
    geo = GeoPoint(lat=-18.9, lon=47.5, accuracy_m=8, source="gps", actor_id=seller.id)
    db_session.add(geo)
    db_session.commit()
    lot = _create_or_lot(db_session, owner_id=seller.id, geo_id=geo.id)

    headers = _auth(client, seller.email)
    response = client.post(
        "/api/v1/trades",
        headers=headers,
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot.id, "quantity": 2, "unit_price": 10000}],
        },
    )
    assert response.status_code == 400
    assert "chaine_or_invalide" in str(response.json())


def test_trades_or_collecteur_to_comptoir_requires_active_license(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur-trade@test.mg",
        phone="0342000011",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    buyer = _create_actor(
        db_session,
        role="comptoir_operator",
        email="comptoir-lic@test.mg",
        phone="0342000012",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    db_session.add(
        CollectorCard(
            actor_id=seller.id,
            issuing_commune_id=commune.id,
            status="active",
            issued_at=datetime.now(timezone.utc),
            validated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=120),
            affiliation_deadline_at=datetime.now(timezone.utc) + timedelta(days=30),
            affiliation_submitted_at=datetime.now(timezone.utc),
        )
    )
    geo = GeoPoint(lat=-18.8, lon=47.6, accuracy_m=6, source="gps", actor_id=seller.id)
    db_session.add(geo)
    db_session.commit()
    lot = _create_or_lot(db_session, owner_id=seller.id, geo_id=geo.id)

    headers = _auth(client, seller.email)
    response = client.post(
        "/api/v1/trades",
        headers=headers,
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot.id, "quantity": 1, "unit_price": 12000}],
        },
    )
    assert response.status_code == 400
    assert "agrement_comptoir_invalide" in str(response.json())


def test_confirm_trade_rechecks_or_license_for_legacy_trade(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur-confirm@test.mg",
        phone="0342000021",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    buyer = _create_actor(
        db_session,
        role="comptoir_operator",
        email="comptoir-confirm@test.mg",
        phone="0342000022",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    db_session.add(
        CollectorCard(
            actor_id=seller.id,
            issuing_commune_id=commune.id,
            status="active",
            issued_at=datetime.now(timezone.utc),
            validated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=120),
            affiliation_deadline_at=datetime.now(timezone.utc) + timedelta(days=30),
            affiliation_submitted_at=datetime.now(timezone.utc),
        )
    )
    geo = GeoPoint(lat=-18.7, lon=47.4, accuracy_m=5, source="gps", actor_id=seller.id)
    db_session.add(geo)
    db_session.commit()
    lot = _create_or_lot(db_session, owner_id=seller.id, geo_id=geo.id)

    tx = TradeTransaction(
        seller_actor_id=seller.id,
        buyer_actor_id=buyer.id,
        status="paid",
        total_amount=20000,
        currency="MGA",
    )
    db_session.add(tx)
    db_session.flush()
    db_session.add(
        TradeTransactionItem(
            transaction_id=tx.id,
            lot_id=lot.id,
            quantity=1,
            unit_price=20000,
            line_amount=20000,
        )
    )
    db_session.commit()

    headers = _auth(client, seller.email)
    response = client.post(f"/api/v1/trades/{tx.id}/confirm", headers=headers)
    assert response.status_code == 400
    assert "agrement_comptoir_invalide" in str(response.json())
