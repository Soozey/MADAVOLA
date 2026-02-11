"""
Tests d'intégration end-to-end pour les workflows complets
"""
from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
from app.models.payment import PaymentProvider, PaymentRequest
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion
from app.models.transaction import TradeTransaction, TradeTransactionItem
from app.territories.importer import import_territory_excel


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
    db_session.flush()
    fokontany = Fokontany(
        version_id=version.id,
        commune_id=commune.id,
        code="010101-001",
        name="Isotry",
        name_normalized="isotry",
    )
    db_session.add(fokontany)
    db_session.commit()
    return region, district, commune, fokontany, version


def _create_actor_with_role(db_session, region, district, commune, fokontany, version, email, phone, role_name="acteur"):
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone=phone,
        email=email,
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        fokontany_id=fokontany.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(
        ActorRole(
            actor_id=actor.id,
            role=role_name,
            status="active",
            valid_from=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    return actor


def test_workflow_actor_signup_to_lot_declaration(client, db_session):
    """Workflow complet: Inscription acteur -> Déclaration lot -> Ledger"""
    region, district, commune, fokontany, version = _seed_territory(db_session)

    # 1. Créer GeoPoint
    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12, source="gps")
    db_session.add(geo)
    db_session.commit()

    # 2. Inscription acteur
    signup = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340000100",
            "email": "rakoto@example.com",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": geo.id,
            "roles": ["orpailleur"],
        },
    )
    assert signup.status_code == 201
    actor_id = signup.json()["id"]
    actor = db_session.query(Actor).filter_by(id=actor_id).first()
    actor.status = "active"
    db_session.commit()

    # 3. Login
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "rakoto@example.com", "password": "secret"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # 4. Déclarer lot
    lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filiere": "OR",
            "product_type": "poudre",
            "unit": "g",
            "quantity": 100.5,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": actor_id,
        },
    )
    assert lot.status_code == 201
    lot_id = lot.json()["id"]

    # 5. Vérifier ledger
    ledger = client.get(
        "/api/v1/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ledger.status_code == 200
    entries = ledger.json()
    assert len(entries) == 1
    assert entries[0]["movement_type"] == "create"
    assert entries[0]["quantity_delta"] == 100.5
    assert entries[0]["lot_id"] == lot_id

    # 6. Vérifier balance
    balance = client.get(
        "/api/v1/ledger/balance",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert balance.status_code == 200
    balances = balance.json()
    assert len(balances) == 1
    assert balances[0]["quantity"] == 100.5


def test_workflow_transaction_payment_invoice(client, db_session):
    """Workflow complet: Transaction -> Paiement -> Facture"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    seller = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "seller@example.com", "0340000200", "acteur"
    )
    buyer = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "buyer@example.com", "0340000201", "acteur"
    )

    # Créer provider
    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.commit()

    # 1. Créer transaction
    transaction = client.post(
        "/api/v1/transactions",
        json={
            "seller_actor_id": seller.id,
            "buyer_actor_id": buyer.id,
            "currency": "MGA",
            "items": [{"lot_id": None, "quantity": 1, "unit_price": 5000}],
        },
    )
    assert transaction.status_code == 201
    txn_id = transaction.json()["id"]

    # 2. Login buyer
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "buyer@example.com", "password": "secret"},
    )
    token = login.json()["access_token"]

    # 3. Initier paiement
    payment = client.post(
        f"/api/v1/transactions/{txn_id}/initiate-payment",
        headers={"Authorization": f"Bearer {token}"},
        json={"provider_code": "mvola"},
    )
    assert payment.status_code == 201

    # 4. Simuler webhook succès
    webhook = client.post(
        "/api/v1/payments/webhooks/mvola",
        json={
            "external_ref": payment.json()["external_ref"],
            "status": "success",
            "operator_ref": "OP123",
        },
    )
    assert webhook.status_code == 200

    # 5. Vérifier facture créée
    invoices = client.get(
        "/api/v1/invoices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invoices.status_code == 200
    invoice_list = invoices.json()
    assert len(invoice_list) == 1
    assert invoice_list[0]["transaction_id"] == txn_id
    assert invoice_list[0]["status"] == "issued"


def test_workflow_lot_transfer_ledger_consistency(client, db_session):
    """Workflow: Transfert lot -> Vérifier cohérence ledger"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    owner1 = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "owner1@example.com", "0340000300", "acteur"
    )
    owner2 = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "owner2@example.com", "0340000301", "acteur"
    )

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12)
    db_session.add(geo)
    db_session.commit()

    # Login owner1
    login1 = client.post(
        "/api/v1/auth/login",
        json={"identifier": "owner1@example.com", "password": "secret"},
    )
    token1 = login1.json()["access_token"]

    # Créer lot
    lot = client.post(
        "/api/v1/lots",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "filiere": "OR",
            "product_type": "poudre",
            "unit": "g",
            "quantity": 200.0,
            "declare_geo_point_id": geo.id,
            "declared_by_actor_id": owner1.id,
        },
    )
    lot_id = lot.json()["id"]

    # Créer payment request pour transfert
    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.commit()

    payment_req = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=owner2.id,
        payee_actor_id=owner1.id,
        amount=1000,
        currency="MGA",
        status="success",
        external_ref="TRANSFER123",
    )
    db_session.add(payment_req)
    db_session.commit()

    # Login owner1 pour transfert
    # Transfert lot
    transfer = client.post(
        f"/api/v1/lots/{lot_id}/transfer",
        headers={"Authorization": f"Bearer {token1}"},
        json={"new_owner_actor_id": owner2.id, "payment_request_id": payment_req.id},
    )
    assert transfer.status_code == 200

    # Vérifier ledger owner1 (sortie)
    ledger1 = client.get(
        "/api/v1/ledger",
        headers={"Authorization": f"Bearer {token1}"},
        params={"actor_id": owner1.id},
    )
    entries1 = ledger1.json()
    assert len(entries1) == 2  # create + transfer out
    transfer_out = [e for e in entries1 if e["movement_type"] == "transfer_out"][0]
    assert transfer_out["quantity_delta"] == -200.0

    # Login owner2
    login2 = client.post(
        "/api/v1/auth/login",
        json={"identifier": "owner2@example.com", "password": "secret"},
    )
    token2 = login2.json()["access_token"]

    # Vérifier ledger owner2 (entrée)
    ledger2 = client.get(
        "/api/v1/ledger",
        headers={"Authorization": f"Bearer {token2}"},
        params={"actor_id": owner2.id},
    )
    entries2 = ledger2.json()
    assert len(entries2) == 1
    assert entries2[0]["movement_type"] == "transfer_in"
    assert entries2[0]["quantity_delta"] == 200.0

    # Vérifier balance owner2
    balance2 = client.get(
        "/api/v1/ledger/balance",
        headers={"Authorization": f"Bearer {token2}"},
    )
    balances2 = balance2.json()
    assert len(balances2) == 1
    assert balances2[0]["quantity"] == 200.0


def test_workflow_export_approval(client, db_session):
    """Workflow: Création export -> Soumission -> Approbation admin"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    exporter = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "exporter@example.com", "0340000400", "acteur"
    )
    admin = _create_actor_with_role(
        db_session, region, district, commune, fokontany, version, "admin@example.com", "0340000401", "admin"
    )

    # Login exporter
    login_exporter = client.post(
        "/api/v1/auth/login",
        json={"identifier": "exporter@example.com", "password": "secret"},
    )
    token_exporter = login_exporter.json()["access_token"]

    # Créer export
    export = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token_exporter}"},
        json={"destination": "Dubai", "total_weight": 50.0},
    )
    assert export.status_code == 201
    export_id = export.json()["id"]
    assert export.json()["status"] == "draft"

    # Soumettre export
    submitted = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_exporter}"},
        json={"status": "submitted"},
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"

    # Exporter ne peut pas approuver
    failed = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_exporter}"},
        json={"status": "approved"},
    )
    assert failed.status_code == 400

    # Admin peut approuver
    login_admin = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@example.com", "password": "secret"},
    )
    token_admin = login_admin.json()["access_token"]

    approved = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
