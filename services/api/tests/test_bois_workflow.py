from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.export import ExportDossier
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
from app.models.pierre import ActorAuthorization
from app.models.bois import EssenceCatalog, WorkflowApproval
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
        db_session.add(ActorRole(actor_id=actor.id, role=role, status="active", valid_from=datetime.now(timezone.utc) - timedelta(days=1)))
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


def _active_auth(db_session, actor_id: int, issuer_id: int, filiere: str = "BOIS"):
    now = datetime.now(timezone.utc)
    db_session.add(
        ActorAuthorization(
            actor_id=actor_id,
            filiere=filiere,
            authorization_type="permit",
            numero=f"AUTH-{filiere}-{actor_id}-{int(now.timestamp())}",
            issued_by_actor_id=issuer_id,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=365),
            status="active",
        )
    )
    db_session.commit()


def test_bois_stock_invariant_after_trade(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(db_session, region, district, commune, version, email="bois.seller@example.com", phone="0345100001", roles=["bois_exploitant"])
    buyer = _create_actor(db_session, region, district, commune, version, email="bois.buyer@example.com", phone="0345100002", roles=["bois_collecteur"])
    admin = _create_actor(db_session, region, district, commune, version, email="bois.admin@example.com", phone="0345100003", roles=["admin"])

    essence = EssenceCatalog(
        code_essence="DAL",
        nom="Dalbergia",
        categorie="C_autre",
        export_autorise=1,
        requires_cites=0,
        rules_json="{}",
        status="active",
        created_by_actor_id=admin.id,
    )
    db_session.add(essence)
    db_session.commit()

    _active_auth(db_session, seller.id, admin.id, "BOIS")
    _active_auth(db_session, buyer.id, admin.id, "BOIS")

    geo = _create_geo(db_session)
    seller_token = _login(client, seller.email)
    buyer_token = _login(client, buyer.email)

    lot_resp = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={
            "filiere": "BOIS",
            "wood_essence_id": essence.id,
            "wood_form": "grume",
            "volume_m3": 5,
            "product_type": "bois_brut",
            "unit": "m3",
            "quantity": 5,
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
            "items": [{"lot_id": lot_resp.json()["id"], "quantity": 2, "unit_price": 1000}],
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

    confirm_resp = client.post(
        f"/api/v1/trades/{trade_id}/confirm",
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert confirm_resp.status_code == 200

    source_lot_id = lot_resp.json()["id"]
    source_ledger = db_session.query(InventoryLedger).filter(InventoryLedger.actor_id == seller.id, InventoryLedger.lot_id == source_lot_id).all()
    assert round(sum(float(x.quantity_delta) for x in source_ledger), 4) == 3.0


def test_transport_scan_marks_suspect_for_unlisted_lot(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    transporteur = _create_actor(db_session, region, district, commune, version, email="bois.transport@example.com", phone="0345200001", roles=["bois_transporteur"])
    controleur = _create_actor(db_session, region, district, commune, version, email="bois.control@example.com", phone="0345200004", roles=["bois_controleur"])
    owner = _create_actor(db_session, region, district, commune, version, email="bois.owner@example.com", phone="0345200002", roles=["bois_exploitant"])
    admin = _create_actor(db_session, region, district, commune, version, email="bois.admin2@example.com", phone="0345200003", roles=["admin"])

    essence = EssenceCatalog(
        code_essence="PIN",
        nom="Pin",
        categorie="C_autre",
        export_autorise=1,
        requires_cites=0,
        rules_json="{}",
        status="active",
        created_by_actor_id=admin.id,
    )
    db_session.add(essence)
    db_session.commit()

    _active_auth(db_session, owner.id, admin.id, "BOIS")

    geo = _create_geo(db_session)
    owner_token = _login(client, owner.email)
    transport_token = _login(client, transporteur.email)
    controller_token = _login(client, controleur.email)

    lot1 = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "filiere": "BOIS",
            "wood_essence_id": essence.id,
            "wood_form": "grume",
            "volume_m3": 2,
            "product_type": "bois_brut",
            "unit": "m3",
            "quantity": 2,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": owner.id,
        },
    ).json()

    lot2 = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "filiere": "BOIS",
            "wood_essence_id": essence.id,
            "wood_form": "grume",
            "volume_m3": 1,
            "product_type": "bois_brut",
            "unit": "m3",
            "quantity": 1,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": owner.id,
        },
    ).json()

    tr = client.post(
        "/api/v1/transports",
        headers={"Authorization": f"Bearer {transport_token}"},
        json={
            "transporter_actor_id": transporteur.id,
            "origin": "010101",
            "destination": "010101",
            "depart_at": datetime.now(timezone.utc).isoformat(),
            "items": [{"lot_id": lot1["id"], "quantity": 2}],
        },
    )
    assert tr.status_code == 201

    verify = client.post(
        f"/api/v1/transports/{tr.json()['id']}/scan_verify",
        headers={"Authorization": f"Bearer {controller_token}"},
        json={"lot_id": lot2["id"]},
    )
    assert verify.status_code == 200
    assert verify.json()["result"] == "suspect"


def test_essence_a_export_blocked_without_exception(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    exporter = _create_actor(db_session, region, district, commune, version, email="bois.exporter@example.com", phone="0345300001", roles=["bois_exportateur"])
    admin = _create_actor(db_session, region, district, commune, version, email="bois.admin3@example.com", phone="0345300002", roles=["admin"])

    essence = EssenceCatalog(
        code_essence="ROS",
        nom="Rosewood",
        categorie="A_protegee",
        export_autorise=0,
        requires_cites=1,
        rules_json="{}",
        status="active",
        created_by_actor_id=admin.id,
    )
    db_session.add(essence)
    db_session.commit()

    _active_auth(db_session, exporter.id, admin.id, "BOIS")
    geo = _create_geo(db_session)
    token = _login(client, exporter.email)

    lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filiere": "BOIS",
            "wood_essence_id": essence.id,
            "wood_form": "planche",
            "product_type": "bois_scie",
            "unit": "m3",
            "quantity": 1,
            "volume_m3": 1,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": exporter.id,
        },
    ).json()

    dossier = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "EU", "total_weight": 1},
    ).json()

    blocked = client.post(
        f"/api/v1/exports/{dossier['id']}/lots",
        headers={"Authorization": f"Bearer {token}"},
        json=[{"lot_id": lot["id"], "quantity_in_export": 1}],
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["message"] == "export_bois_bloque_essence_a"

    db_session.add(
        WorkflowApproval(
            filiere="BOIS",
            workflow_type="export_exception",
            entity_type="lot_export_exception",
            entity_id=lot["id"],
            status="approved",
            reference_texte="TODO LEGAL",
            requested_by_actor_id=exporter.id,
            decided_by_actor_id=admin.id,
            decided_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    admin_token = _login(client, admin.email)
    classify = client.patch(
        f"/api/v1/lots/{lot['id']}/wood-classification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "wood_classification": "LEGAL_EXPORTABLE",
            "cites_laf_status": "approved",
            "cites_ndf_status": "approved",
            "cites_international_status": "approved",
            "notes": "Validation CITES completee",
        },
    )
    assert classify.status_code == 200

    allowed = client.post(
        f"/api/v1/exports/{dossier['id']}/lots",
        headers={"Authorization": f"Bearer {token}"},
        json=[{"lot_id": lot["id"], "quantity_in_export": 1}],
    )
    assert allowed.status_code == 200


def test_expired_authorization_blocks_bois_trade_and_export(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor(db_session, region, district, commune, version, email="bois.expired@example.com", phone="0345400001", roles=["bois_collecteur", "bois_exportateur"])
    buyer = _create_actor(db_session, region, district, commune, version, email="bois.active@example.com", phone="0345400002", roles=["bois_transformateur"])
    admin = _create_actor(db_session, region, district, commune, version, email="bois.admin4@example.com", phone="0345400003", roles=["admin"])

    now = datetime.now(timezone.utc)
    db_session.add(
        ActorAuthorization(
            actor_id=seller.id,
            filiere="BOIS",
            authorization_type="permit",
            numero="BOIS-EXPIRED-1",
            issued_by_actor_id=admin.id,
            valid_from=now - timedelta(days=50),
            valid_to=now - timedelta(days=1),
            status="active",
        )
    )
    _active_auth(db_session, buyer.id, admin.id, "BOIS")

    essence = EssenceCatalog(
        code_essence="TEK",
        nom="Teck",
        categorie="C_autre",
        export_autorise=1,
        requires_cites=0,
        rules_json="{}",
        status="active",
        created_by_actor_id=admin.id,
    )
    db_session.add(essence)
    db_session.commit()

    geo = _create_geo(db_session)
    token = _login(client, seller.email)

    # create lot directly to isolate trade/export checks
    lot = Lot(
        filiere="BOIS",
        wood_essence_id=essence.id,
        wood_form="planche",
        quantity=2,
        unit="m3",
        volume_m3=2,
        product_type="bois_scie",
        declared_by_actor_id=seller.id,
        current_owner_actor_id=seller.id,
        status="available",
        declare_geo_point_id=geo.id,
    )
    db_session.add(lot)
    db_session.commit()

    trade = client.post(
        "/api/v1/trades",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": lot.id, "quantity": 1, "unit_price": 1000}],
        },
    )
    assert trade.status_code == 400
    assert trade.json()["detail"]["message"] == "autorisation_expiree"

    export_resp = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "EU", "total_weight": 1},
    )
    assert export_resp.status_code == 201

    link = client.post(
        f"/api/v1/exports/{export_resp.json()['id']}/lots",
        headers={"Authorization": f"Bearer {token}"},
        json=[{"lot_id": lot.id, "quantity_in_export": 1}],
    )
    assert link.status_code == 400
    assert link.json()["detail"]["message"] == "autorisation_expiree"


def test_rbac_artisan_cannot_create_permit_and_controller_cannot_create_lot(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    artisan = _create_actor(db_session, region, district, commune, version, email="bois.artisan@example.com", phone="0345500001", roles=["bois_artisan"])
    controller = _create_actor(db_session, region, district, commune, version, email="bois.ctrl@example.com", phone="0345500002", roles=["bois_controleur"])
    target = _create_actor(db_session, region, district, commune, version, email="bois.target@example.com", phone="0345500003", roles=["bois_exploitant"])
    admin = _create_actor(db_session, region, district, commune, version, email="bois.admin5@example.com", phone="0345500004", roles=["admin"])

    essence = EssenceCatalog(
        code_essence="EUC",
        nom="Eucalyptus",
        categorie="B_artisanale",
        export_autorise=1,
        requires_cites=0,
        rules_json="{}",
        status="active",
        created_by_actor_id=admin.id,
    )
    db_session.add(essence)
    db_session.commit()

    artisan_token = _login(client, artisan.email)
    denied_permit = client.post(
        f"/api/v1/actors/{target.id}/authorizations",
        headers={"Authorization": f"Bearer {artisan_token}"},
        json={
            "filiere": "BOIS",
            "authorization_type": "permit",
            "numero": "PERMIT-ART-1",
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_to": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        },
    )
    assert denied_permit.status_code == 400
    assert denied_permit.json()["detail"]["message"] == "role_insuffisant"

    _active_auth(db_session, controller.id, admin.id, "BOIS")
    controller_token = _login(client, controller.email)
    geo = _create_geo(db_session)
    denied_lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {controller_token}"},
        json={
            "filiere": "BOIS",
            "wood_essence_id": essence.id,
            "wood_form": "grume",
            "volume_m3": 1,
            "product_type": "bois_brut",
            "unit": "m3",
            "quantity": 1,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": controller.id,
        },
    )
    assert denied_lot.status_code == 400
    assert denied_lot.json()["detail"]["message"] == "role_insuffisant"
