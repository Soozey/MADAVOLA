"""Minimal E2E CLI for MADAVOLA Phase 2.

Runs in-process against FastAPI app with sqlite in-memory DB.
Checks:
- Happy path BOIS (actor->lot->transport->scan->transformation->trade->export validate)
- Blocked path BOIS (essence A export blocked)
- Happy path PIERRE (lot->trade->export)
- Blocked path PIERRE (rbac trade blocked)

Usage:
  set PYTHONPATH=services/api
  python services/api/scripts/e2e_cli.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long")
os.environ.setdefault("DOCUMENT_STORAGE_DIR", "services/api/tests/.tmp_uploads")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.db import get_db
from app.main import create_app
from app.models.base import Base
from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.lot import InventoryLedger, Lot
from app.models.territory import TerritoryVersion, Region, District, Commune
from app.models.pierre import ProductCatalog, ActorAuthorization
from app.models.bois import EssenceCatalog


class E2EError(RuntimeError):
    pass


def assert_ok(resp, code=200, label=""):
    if resp.status_code != code:
        raise E2EError(f"{label} expected {code}, got {resp.status_code}: {resp.text}")


def _balance(db, actor_id: int, lot_id: int) -> float:
    rows = (
        db.query(InventoryLedger.quantity_delta)
        .filter(InventoryLedger.actor_id == actor_id, InventoryLedger.lot_id == lot_id)
        .all()
    )
    return round(sum(float(r[0]) for r in rows), 6)


def _assert_balance(db, actor_id: int, lot_id: int, expected: float, label: str) -> None:
    got = _balance(db, actor_id, lot_id)
    if abs(got - expected) > 1e-6:
        raise E2EError(f"{label} balance mismatch expected={expected} got={got}")


def _assert_lot_status(db, lot_id: int, expected: str, label: str) -> None:
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise E2EError(f"{label} lot not found")
    if lot.status != expected:
        raise E2EError(f"{label} status mismatch expected={expected} got={lot.status}")


def seed_territory(db):
    version = TerritoryVersion(
        version_tag="v1",
        source_filename="seed.xlsx",
        checksum_sha256="seed",
        status="active",
        imported_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()
    region = Region(version_id=version.id, code="01", name="Analamanga", name_normalized="analamanga")
    db.add(region)
    db.flush()
    district = District(version_id=version.id, region_id=region.id, code="0101", name="Antananarivo", name_normalized="antananarivo")
    db.add(district)
    db.flush()
    commune = Commune(version_id=version.id, district_id=district.id, code="010101", name="Antananarivo I", name_normalized="antananarivo i")
    db.add(commune)
    db.commit()
    return region, district, commune, version


def create_actor(db, region, district, commune, version, *, email, phone, roles):
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
    db.add(actor)
    db.flush()
    db.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    for role in roles:
        db.add(ActorRole(actor_id=actor.id, role=role, status="active", valid_from=datetime.now(timezone.utc) - timedelta(days=1)))
    db.commit()
    return actor


def create_auth(db, actor_id, issuer_id, filiere):
    now = datetime.now(timezone.utc)
    db.add(
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
    db.commit()


def login(client, email):
    r = client.post("/api/v1/auth/login", json={"identifier": email, "password": "secret"})
    assert_ok(r, 200, "login")
    return r.json()["access_token"]


def run():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    app = create_app()

    def _override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    region, district, commune, version = seed_territory(db)

    admin = create_actor(db, region, district, commune, version, email="admin.e2e@example.com", phone="0348000001", roles=["admin"])
    bois_exp = create_actor(db, region, district, commune, version, email="bois.exp@example.com", phone="0348000002", roles=["bois_exploitant"])
    bois_col = create_actor(db, region, district, commune, version, email="bois.col@example.com", phone="0348000003", roles=["bois_collecteur"])
    bois_trn = create_actor(db, region, district, commune, version, email="bois.trn@example.com", phone="0348000004", roles=["bois_transporteur", "bois_controleur"])
    bois_tfm = create_actor(db, region, district, commune, version, email="bois.tfm@example.com", phone="0348000009", roles=["bois_transformateur"])
    bois_exp2 = create_actor(db, region, district, commune, version, email="bois.expo@example.com", phone="0348000005", roles=["bois_exportateur", "bois_douanes"])

    pierre_exp = create_actor(db, region, district, commune, version, email="pierre.exp@example.com", phone="0348000006", roles=["pierre_exploitant"])
    pierre_col = create_actor(db, region, district, commune, version, email="pierre.col@example.com", phone="0348000007", roles=["pierre_collecteur"])
    pierre_bad = create_actor(db, region, district, commune, version, email="pierre.bad@example.com", phone="0348000008", roles=["pierre_exportateur"])

    create_auth(db, bois_exp.id, admin.id, "BOIS")
    create_auth(db, bois_col.id, admin.id, "BOIS")
    create_auth(db, bois_tfm.id, admin.id, "BOIS")
    create_auth(db, bois_exp2.id, admin.id, "BOIS")
    create_auth(db, pierre_exp.id, admin.id, "PIERRE")
    create_auth(db, pierre_col.id, admin.id, "PIERRE")
    create_auth(db, pierre_bad.id, admin.id, "PIERRE")

    essence_ok = EssenceCatalog(code_essence="TEK", nom="Teck", categorie="C_autre", export_autorise=1, requires_cites=0, rules_json="{}", status="active", created_by_actor_id=admin.id)
    essence_block = EssenceCatalog(code_essence="ROS", nom="Rosewood", categorie="A_protegee", export_autorise=0, requires_cites=1, rules_json="{}", status="active", created_by_actor_id=admin.id)
    db.add_all([essence_ok, essence_block])

    product = ProductCatalog(code="P-E2E", nom="Quartz", famille="PIERRE", filiere="PIERRE", sous_filiere="GEMME", allowed_units_json='["carat"]', required_attributes_json='["couleur"]', export_restricted=0, export_rules_json='{}', status="active", created_by_actor_id=admin.id)
    db.add(product)
    db.commit()

    tok_bois_exp = login(client, bois_exp.email)
    tok_bois_col = login(client, bois_col.email)
    tok_bois_trn = login(client, bois_trn.email)
    tok_bois_tfm = login(client, bois_tfm.email)
    tok_bois_exp2 = login(client, bois_exp2.email)
    tok_pierre_exp = login(client, pierre_exp.email)
    tok_pierre_col = login(client, pierre_col.email)

    geo = client.post('/api/v1/geo-points', headers={"Authorization": f"Bearer {tok_bois_exp}"}, json={"lat": -18.87, "lon": 47.50, "accuracy_m": 10, "source": "e2e"})
    assert_ok(geo, 201, "geo")
    geo_id = geo.json()['id']

    # Happy BOIS
    lot_bois = client.post('/api/v1/lots', headers={"Authorization": f"Bearer {tok_bois_exp}"}, json={
        "filiere": "BOIS", "wood_essence_id": essence_ok.id, "wood_form": "grume", "volume_m3": 2,
        "product_type": "bois_brut", "unit": "m3", "quantity": 2,
        "declare_geo_point_id": geo_id, "declared_by_actor_id": bois_exp.id,
    })
    assert_ok(lot_bois, 201, "bois lot")
    lot_bois_id = lot_bois.json()['id']
    _assert_balance(db, bois_exp.id, lot_bois_id, 2.0, "bois create")

    tr = client.post('/api/v1/transports', headers={"Authorization": f"Bearer {tok_bois_trn}"}, json={
        "transporter_actor_id": bois_trn.id, "origin": "A", "destination": "B", "depart_at": datetime.now(timezone.utc).isoformat(),
        "items": [{"lot_id": lot_bois_id, "quantity": 2}],
    })
    assert_ok(tr, 201, "transport create")
    tr_id = tr.json()['id']
    sv = client.post(f'/api/v1/transports/{tr_id}/scan_verify', headers={"Authorization": f"Bearer {tok_bois_trn}"}, json={"lot_id": lot_bois_id})
    assert_ok(sv, 200, "transport scan")

    # transfer to transformateur before transformation
    trade_pre = client.post('/api/v1/trades', headers={"Authorization": f"Bearer {tok_bois_exp}"}, json={
        "seller_actor_id": bois_exp.id, "buyer_actor_id": bois_tfm.id, "currency": "MGA",
        "items": [{"lot_id": lot_bois_id, "quantity": 2.0, "unit_price": 900}],
    })
    assert_ok(trade_pre, 201, "trade pre-transform")
    tpre = trade_pre.json()['id']
    assert_ok(client.post(f'/api/v1/trades/{tpre}/pay', headers={"Authorization": f"Bearer {tok_bois_tfm}"}, json={"payment_mode": "cash_declared"}), 200, "trade pay pre-transform")
    assert_ok(client.post(f'/api/v1/trades/{tpre}/confirm', headers={"Authorization": f"Bearer {tok_bois_tfm}"}), 200, "trade confirm pre-transform")
    _assert_balance(db, bois_exp.id, lot_bois_id, 0.0, "bois seller post-transfer")
    _assert_balance(db, bois_tfm.id, lot_bois_id, 2.0, "bois tfm post-transfer")

    tf = client.post('/api/v1/transformations', headers={"Authorization": f"Bearer {tok_bois_tfm}"}, json={
        "operation_type": "sciage",
        "input_lot_ids": [lot_bois_id],
        "outputs": [{"quantity": 1.5, "unit": "m3", "wood_form": "planche"}, {"quantity": 0.5, "unit": "m3", "wood_form": "lot_scie"}],
    })
    assert_ok(tf, 201, "transformation")
    output_lot = tf.json()['output_lot_ids'][0]
    output_lot_2 = tf.json()['output_lot_ids'][1]
    _assert_balance(db, bois_tfm.id, lot_bois_id, 0.0, "bois tfm input after transform")
    _assert_balance(db, bois_tfm.id, output_lot, 1.5, "bois tfm output1 after transform")
    _assert_balance(db, bois_tfm.id, output_lot_2, 0.5, "bois tfm output2 after transform")
    _assert_lot_status(db, lot_bois_id, "transformed", "bois input lot")

    trade = client.post('/api/v1/trades', headers={"Authorization": f"Bearer {tok_bois_tfm}"}, json={
        "seller_actor_id": bois_tfm.id, "buyer_actor_id": bois_exp2.id, "currency": "MGA",
        "items": [{"lot_id": output_lot, "quantity": 1.0, "unit_price": 1000}],
    })
    assert_ok(trade, 201, "trade create bois")
    tid = trade.json()['id']
    assert_ok(client.post(f'/api/v1/trades/{tid}/pay', headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json={"payment_mode": "cash_declared"}), 200, "trade pay bois")
    assert_ok(client.post(f'/api/v1/trades/{tid}/confirm', headers={"Authorization": f"Bearer {tok_bois_exp2}"}), 200, "trade confirm bois")
    _assert_balance(db, bois_tfm.id, output_lot, 0.5, "bois tfm output1 after sale")
    exporter_child_lot = (
        db.query(Lot)
        .filter(Lot.parent_lot_id == output_lot, Lot.current_owner_actor_id == bois_exp2.id)
        .order_by(Lot.id.desc())
        .first()
    )
    if not exporter_child_lot:
        raise E2EError("expected buyer child lot after partial bois trade")
    exportable_lot_id = exporter_child_lot.id
    _assert_balance(db, bois_exp2.id, exportable_lot_id, 1.0, "bois exporter child lot after buy")

    exp = client.post('/api/v1/exports', headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json={"destination": "EU", "total_weight": 1})
    assert_ok(exp, 201, "export create bois")
    exp_id = exp.json()['id']
    assert_ok(
        client.post(
            f'/api/v1/exports/{exp_id}/lots',
            headers={"Authorization": f"Bearer {tok_bois_exp2}"},
            json=[{"lot_id": exportable_lot_id, "quantity_in_export": 1.0}],
        ),
        200,
        "export link bois lot",
    )
    assert_ok(
        client.post(
            f'/api/v1/exports/{exp_id}/submit',
            headers={"Authorization": f"Bearer {tok_bois_exp2}"},
            json={"status": "submitted"},
        ),
        200,
        "export submit bois",
    )
    assert_ok(
        client.post(
            f'/api/v1/exports/{exp_id}/validate',
            headers={"Authorization": f"Bearer {tok_bois_exp2}"},
            json={"step_code": "mines", "decision": "approved"},
        ),
        200,
        "export validate mines",
    )
    assert_ok(
        client.post(
            f'/api/v1/exports/{exp_id}/validate',
            headers={"Authorization": f"Bearer {tok_bois_exp2}"},
            json={"step_code": "douanes", "decision": "approved", "seal_number": "SEAL-E2E-001"},
        ),
        200,
        "export validate douanes",
    )
    _assert_lot_status(db, exportable_lot_id, "exported", "bois output lot exported")

    pre_bal = _balance(db, bois_exp2.id, exportable_lot_id)
    blocked_trade = client.post('/api/v1/trades', headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json={
        "seller_actor_id": bois_exp2.id, "buyer_actor_id": bois_col.id, "currency": "MGA",
        "items": [{"lot_id": exportable_lot_id, "quantity": 0.5, "unit_price": 1200}],
    })
    if blocked_trade.status_code != 400:
        raise E2EError(f"expected exported lot transfer blocked, got {blocked_trade.status_code}")
    post_bal = _balance(db, bois_exp2.id, exportable_lot_id)
    if abs(pre_bal - post_bal) > 1e-6:
        raise E2EError(f"ledger mutated on blocked exported transfer pre={pre_bal} post={post_bal}")

    # Blocked BOIS export essence A
    lot_block = client.post('/api/v1/lots', headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json={
        "filiere": "BOIS", "wood_essence_id": essence_block.id, "wood_form": "planche", "volume_m3": 1,
        "product_type": "bois_scie", "unit": "m3", "quantity": 1,
        "declare_geo_point_id": geo_id, "declared_by_actor_id": bois_exp2.id,
    })
    assert_ok(lot_block, 201, "bois lot blocked")
    exp_block = client.post('/api/v1/exports', headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json={"destination": "EU", "total_weight": 1})
    assert_ok(exp_block, 201, "export create blocked")
    link_block = client.post(f"/api/v1/exports/{exp_block.json()['id']}/lots", headers={"Authorization": f"Bearer {tok_bois_exp2}"}, json=[{"lot_id": lot_block.json()['id'], "quantity_in_export": 1}])
    if link_block.status_code != 400:
        raise E2EError(f"expected blocked export for essence A, got {link_block.status_code}")

    # Happy PIERRE
    lot_p = client.post('/api/v1/lots', headers={"Authorization": f"Bearer {tok_pierre_exp}"}, json={
        "filiere": "PIERRE", "sous_filiere": "GEMME", "product_catalog_id": product.id,
        "attributes": {"couleur": "bleu"}, "product_type": "quartz", "unit": "carat", "quantity": 10,
        "declare_geo_point_id": geo_id, "declared_by_actor_id": pierre_exp.id,
    })
    assert_ok(lot_p, 201, "pierre lot")
    lot_p_id = lot_p.json()['id']
    tr_p = client.post('/api/v1/trades', headers={"Authorization": f"Bearer {tok_pierre_exp}"}, json={
        "seller_actor_id": pierre_exp.id, "buyer_actor_id": pierre_col.id, "currency": "MGA",
        "items": [{"lot_id": lot_p_id, "quantity": 5, "unit_price": 2000}],
    })
    assert_ok(tr_p, 201, "pierre trade")
    tid_p = tr_p.json()['id']
    assert_ok(client.post(f'/api/v1/trades/{tid_p}/pay', headers={"Authorization": f"Bearer {tok_pierre_col}"}, json={"payment_mode": "cash_declared"}), 200, "trade pay pierre")
    assert_ok(client.post(f'/api/v1/trades/{tid_p}/confirm', headers={"Authorization": f"Bearer {tok_pierre_col}"}), 200, "trade confirm pierre")
    _assert_balance(db, pierre_exp.id, lot_p_id, 5.0, "pierre seller post-trade")
    pierre_child_lot = (
        db.query(Lot)
        .filter(Lot.parent_lot_id == lot_p_id, Lot.current_owner_actor_id == pierre_col.id)
        .order_by(Lot.id.desc())
        .first()
    )
    if not pierre_child_lot:
        raise E2EError("expected buyer child lot after partial pierre trade")
    _assert_balance(db, pierre_col.id, pierre_child_lot.id, 5.0, "pierre buyer post-trade")

    # Blocked PIERRE RBAC path exploitant -> exportateur forbidden
    tok_pierre_bad = login(client, pierre_bad.email)
    bad = client.post('/api/v1/trades', headers={"Authorization": f"Bearer {tok_pierre_exp}"}, json={
        "seller_actor_id": pierre_exp.id, "buyer_actor_id": pierre_bad.id, "currency": "MGA",
        "items": [{"lot_id": lot_p_id, "quantity": 1, "unit_price": 1000}],
    })
    if bad.status_code != 400:
        raise E2EError(f"expected blocked pierre trade path, got {bad.status_code}")

    # Notifications endpoint smoke
    n = client.post('/api/v1/notifications/run-expiry-reminders?thresholds=30,7,1', headers={"Authorization": f"Bearer {login(client, admin.email)}"})
    assert_ok(n, 200, "notifications run")

    print("E2E CLI PASS: OR/PIERRE/BOIS critical workflows checked")


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:  # noqa: BLE001
        print(f"E2E CLI FAIL: {exc}")
        raise
