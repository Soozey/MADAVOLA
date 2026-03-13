from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
from app.models.pierre import ActorAuthorization, ProductCatalog
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


def _create_actor(db_session, region, district, commune, version, *, email: str, phone: str, roles: list[str]):
    actor = Actor(
        type_personne="physique",
        nom=email.split("@")[0],
        prenoms="Test",
        telephone=phone,
        email=email,
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
    for role in roles:
        db_session.add(
            ActorRole(
                actor_id=actor.id,
                role=role,
                status="active",
                valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
    db_session.commit()
    return actor


def _login(client, email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"identifier": email, "password": "secret"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_geo(db_session) -> GeoPoint:
    geo = GeoPoint(lat=-18.8792, lon=47.5079, accuracy_m=10)
    db_session.add(geo)
    db_session.commit()
    return geo


def _create_catalog_and_auth(db_session, actor_id: int, created_by_actor_id: int):
    now = datetime.now(timezone.utc)
    product = ProductCatalog(
        code=f"P-GEM-{actor_id}",
        nom="Quartz brut",
        famille="PIERRE",
        filiere="PIERRE",
        sous_filiere="GEMME",
        allowed_units_json='["carat","g"]',
        required_attributes_json='["couleur","clarte"]',
        export_restricted=0,
        export_rules_json="{}",
        status="active",
        created_by_actor_id=created_by_actor_id,
    )
    db_session.add(product)
    db_session.flush()
    db_session.add(
        ActorAuthorization(
            actor_id=actor_id,
            filiere="PIERRE",
            authorization_type="carte_pierre",
            numero=f"AUTH-{actor_id}-{int(now.timestamp())}",
            issued_by_actor_id=created_by_actor_id,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
            status="active",
        )
    )
    db_session.commit()
    return product


def test_pierre_trade_keeps_ledger_coherent(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="seller.pierre@example.com",
        phone="0341111001",
        roles=["pierre_exploitant"],
    )
    buyer = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="buyer.pierre@example.com",
        phone="0341111002",
        roles=["pierre_collecteur"],
    )
    admin = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="admin.pierre@example.com",
        phone="0341111003",
        roles=["admin"],
    )

    product = _create_catalog_and_auth(db_session, seller.id, admin.id)
    _create_catalog_and_auth(db_session, buyer.id, admin.id)

    geo = _create_geo(db_session)
    seller_token = _login(client, seller.email)
    buyer_token = _login(client, buyer.email)

    lot_resp = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "filiere": "PIERRE",
            "sous_filiere": "GEMME",
            "product_catalog_id": product.id,
            "attributes": {"couleur": "bleu", "clarte": "A"},
            "product_type": "quartz",
            "unit": "carat",
            "quantity": 10,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": seller.id,
        },
    )
    assert lot_resp.status_code == 201
    lot_id = lot_resp.json()["id"]

    trade_resp = client.post(
        "/api/v1/trades",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot_id, "quantity": 4, "unit_price": 1000}],
        },
    )
    assert trade_resp.status_code == 201
    trade_id = trade_resp.json()["id"]

    pay_resp = client.post(
        f"/api/v1/trades/{trade_id}/pay",
        headers={"Authorization": f"Bearer {buyer_token}"},
        json={"payment_mode": "cash_declared"},
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["status"] == "paid"

    confirm_resp = client.post(
        f"/api/v1/trades/{trade_id}/confirm",
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "transferred"

    parent = db_session.query(Lot).filter(Lot.id == lot_id).first()
    assert parent is not None
    assert float(parent.quantity) == 6.0
    assert parent.current_owner_actor_id == seller.id

    child = (
        db_session.query(Lot)
        .filter(Lot.parent_lot_id == lot_id, Lot.current_owner_actor_id == buyer.id)
        .order_by(Lot.id.desc())
        .first()
    )
    assert child is not None
    assert float(child.quantity) == 4.0

    seller_parent_sum = (
        db_session.query(InventoryLedger)
        .filter(InventoryLedger.actor_id == seller.id, InventoryLedger.lot_id == lot_id)
        .all()
    )
    assert round(sum(float(x.quantity_delta) for x in seller_parent_sum), 4) == 6.0

    buyer_child_sum = (
        db_session.query(InventoryLedger)
        .filter(InventoryLedger.actor_id == buyer.id, InventoryLedger.lot_id == child.id)
        .all()
    )
    assert round(sum(float(x.quantity_delta) for x in buyer_child_sum), 4) == 4.0


def test_pierre_trade_rbac_denies_unauthorized_path(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="seller.rbac@example.com",
        phone="0341112001",
        roles=["pierre_exploitant"],
    )
    buyer = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="buyer.rbac@example.com",
        phone="0341112002",
        roles=["pierre_exportateur"],
    )
    admin = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="admin.rbac@example.com",
        phone="0341112003",
        roles=["admin"],
    )

    product = _create_catalog_and_auth(db_session, seller.id, admin.id)
    _create_catalog_and_auth(db_session, buyer.id, admin.id)

    geo = _create_geo(db_session)
    seller_token = _login(client, seller.email)

    lot_resp = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "filiere": "PIERRE",
            "sous_filiere": "GEMME",
            "product_catalog_id": product.id,
            "attributes": {"couleur": "vert", "clarte": "B"},
            "product_type": "tourmaline",
            "unit": "carat",
            "quantity": 2,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": seller.id,
        },
    )
    assert lot_resp.status_code == 201

    trade_resp = client.post(
        "/api/v1/trades",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot_resp.json()["id"], "quantity": 2, "unit_price": 2000}],
        },
    )
    assert trade_resp.status_code == 400
    assert trade_resp.json()["detail"]["message"] == "rbac_trade_pierre_refuse"


def test_exported_lot_cannot_be_traded(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    exporter = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="exporter.block@example.com",
        phone="0341113001",
        roles=["pierre_exportateur"],
    )
    buyer = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="buyer.block@example.com",
        phone="0341113002",
        roles=["pierre_collecteur"],
    )
    admin = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="admin.block@example.com",
        phone="0341113003",
        roles=["admin"],
    )

    product = _create_catalog_and_auth(db_session, exporter.id, admin.id)
    _create_catalog_and_auth(db_session, buyer.id, admin.id)

    geo = _create_geo(db_session)
    exporter_token = _login(client, exporter.email)

    lot_resp = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {exporter_token}"},
        json={
            "filiere": "PIERRE",
            "sous_filiere": "GEMME",
            "product_catalog_id": product.id,
            "attributes": {"couleur": "rouge", "clarte": "A"},
            "product_type": "rubis",
            "unit": "carat",
            "quantity": 3,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": exporter.id,
        },
    )
    assert lot_resp.status_code == 201
    lot_id = lot_resp.json()["id"]

    export_resp = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {exporter_token}"},
        json={"destination": "Dubai", "destination_country": "AE", "total_weight": 3},
    )
    assert export_resp.status_code == 201
    export_id = export_resp.json()["id"]

    link_resp = client.post(
        f"/api/v1/exports/{export_id}/lots",
        headers={"Authorization": f"Bearer {exporter_token}"},
        json=[{"lot_id": lot_id, "quantity_in_export": 3}],
    )
    assert link_resp.status_code == 200

    validate_resp = client.post(
        f"/api/v1/exports/{export_id}/validate",
        headers={"Authorization": f"Bearer {exporter_token}"},
        json={"step_code": "douanes", "decision": "approved", "seal_number": "S-P-0001"},
    )
    assert validate_resp.status_code == 200
    assert validate_resp.json()["status"] == "exported"

    blocked_trade = client.post(
        "/api/v1/trades",
        headers={"Authorization": f"Bearer {exporter_token}"},
        json={
            "seller_actor_id": exporter.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot_id, "quantity": 1, "unit_price": 3000}],
        },
    )
    assert blocked_trade.status_code == 400
    assert blocked_trade.json()["detail"]["message"] == "lot_exported_transfer_blocked"


def test_expired_authorization_blocks_trade_and_export_and_reminders(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    expired_actor = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="expired.auth@example.com",
        phone="0341114001",
        roles=["pierre_collecteur", "pierre_exportateur"],
    )
    active_buyer = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="active.auth@example.com",
        phone="0341114002",
        roles=["pierre_collecteur"],
    )
    admin = _create_actor(
        db_session,
        region,
        district,
        commune,
        version,
        email="admin.auth@example.com",
        phone="0341114003",
        roles=["admin"],
    )

    now = datetime.now(timezone.utc)
    db_session.add(
        ActorAuthorization(
            actor_id=expired_actor.id,
            filiere="PIERRE",
            authorization_type="carte_pierre",
            numero="AUTH-EXPIRED-1",
            issued_by_actor_id=admin.id,
            valid_from=now - timedelta(days=60),
            valid_to=now - timedelta(days=1),
            status="active",
        )
    )
    db_session.add(
        ActorAuthorization(
            actor_id=active_buyer.id,
            filiere="PIERRE",
            authorization_type="carte_pierre",
            numero="AUTH-ACTIVE-1",
            issued_by_actor_id=admin.id,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
            status="active",
        )
    )
    expiring_auth = ActorAuthorization(
        actor_id=active_buyer.id,
        filiere="PIERRE",
        authorization_type="carte_pierre",
        numero="AUTH-REMINDER-7",
        issued_by_actor_id=admin.id,
        valid_from=now - timedelta(days=10),
        valid_to=now + timedelta(days=7),
        status="active",
    )
    db_session.add(expiring_auth)

    lot = Lot(
        filiere="PIERRE",
        sous_filiere="GEMME",
        product_type="saphir",
        unit="carat",
        quantity=5,
        declared_by_actor_id=expired_actor.id,
        current_owner_actor_id=expired_actor.id,
        status="available",
        declare_geo_point_id=_create_geo(db_session).id,
    )
    db_session.add(lot)
    db_session.commit()

    expired_token = _login(client, expired_actor.email)
    admin_token = _login(client, admin.email)

    trade_resp = client.post(
        "/api/v1/trades",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={
            "seller_actor_id": expired_actor.id,
            "buyer_actor_id": active_buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot.id, "quantity": 2, "unit_price": 5000}],
        },
    )
    assert trade_resp.status_code == 400
    assert trade_resp.json()["detail"]["message"] == "autorisation_expiree"

    export_resp = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={"destination": "Dubai", "destination_country": "AE", "total_weight": 5},
    )
    assert export_resp.status_code == 201
    export_id = export_resp.json()["id"]

    link_resp = client.post(
        f"/api/v1/exports/{export_id}/lots",
        headers={"Authorization": f"Bearer {expired_token}"},
        json=[{"lot_id": lot.id, "quantity_in_export": 5}],
    )
    assert link_resp.status_code == 400
    assert link_resp.json()["detail"]["message"] == "autorisation_expiree"

    reminder_resp = client.post(
        "/api/v1/notifications/run-expiry-reminders?thresholds=7",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reminder_resp.status_code == 200
    assert reminder_resp.json()["created_notifications"] >= 1

    list_resp = client.get(
        f"/api/v1/notifications?actor_id={active_buyer.id}",
        headers={"Authorization": f"Bearer {_login(client, active_buyer.email)}"},
    )
    assert list_resp.status_code == 200
    assert any("expire dans 7" in row["message"] for row in list_resp.json())
