from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.gold_ops import ExportChecklistItem
from app.models.lot import Lot
from app.models.payment import PaymentProvider, PaymentRequest
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
    commune = Commune(version_id=version.id, district_id=district.id, code="010101", name="Antananarivo I", name_normalized="antananarivo i")
    db_session.add(commune)
    db_session.commit()
    return region, district, commune, version


def _create_actor_with_role(db_session, region, district, commune, version, email, role):
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone=f"034{abs(hash(email)) % 10000000:07d}",
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
    db_session.add(ActorRole(actor_id=actor.id, role=role, status="active", valid_from=datetime.now(timezone.utc)))
    db_session.commit()
    return actor


def test_orpailleur_cannot_create_export(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    orpailleur = _create_actor_with_role(db_session, region, district, commune, version, "orpailleur-exp@example.com", "orpailleur")

    login = client.post("/api/v1/auth/login", json={"identifier": orpailleur.email, "password": "secret"})
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "Dubai", "total_weight": 2.0},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "export_direct_orpailleur_interdit"


def test_transfer_or_without_transport_marks_suspect(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    seller = _create_actor_with_role(db_session, region, district, commune, version, "seller-or@example.com", "collecteur")
    buyer = _create_actor_with_role(db_session, region, district, commune, version, "buyer-or@example.com", "comptoir_operator")

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=10, actor_id=seller.id)
    db_session.add(geo)
    db_session.flush()
    lot = Lot(
        filiere="OR",
        product_type="or_brut",
        unit="g",
        quantity=Decimal("10.0"),
        declared_by_actor_id=seller.id,
        current_owner_actor_id=seller.id,
        status="available",
        declare_geo_point_id=geo.id,
        qr_code="LOT-QR-1",
    )
    db_session.add(lot)
    provider = PaymentProvider(code="mvola", name="Mvola", enabled=True)
    db_session.add(provider)
    db_session.flush()
    payment = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=buyer.id,
        payee_actor_id=seller.id,
        amount=Decimal("1000"),
        currency="MGA",
        status="success",
        external_ref="pay-transfer-or-1",
    )
    db_session.add(payment)
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": seller.email, "password": "secret"})
    token = login.json()["access_token"]
    response = client.post(
        f"/api/v1/lots/{lot.id}/transfer",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_owner_actor_id": buyer.id, "payment_request_id": payment.id},
    )
    assert response.status_code == 400
    refreshed = db_session.query(Lot).filter_by(id=lot.id).first()
    assert refreshed.status == "suspect"


def test_canonical_export_step_immutable(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "bijoutier-exp@example.com", "bijoutier")

    login = client.post("/api/v1/auth/login", json={"identifier": actor.email, "password": "secret"})
    token = login.json()["access_token"]
    created = client.post(
        "/api/v1/exports",
        headers={"Authorization": f"Bearer {token}"},
        json={"destination": "Dubai", "total_weight": 3.0},
    )
    assert created.status_code == 201
    export_id = created.json()["id"]
    jumped = client.patch(
        f"/api/v1/exports/{export_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "tested_certified"},
    )
    assert jumped.status_code == 400
    assert jumped.json()["detail"]["message"] == "transition_export_invalide"


def test_tax_paid_requires_confirmed_payment(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    admin = _create_actor_with_role(db_session, region, district, commune, version, "admin-tax-ext@example.com", "admin")

    login = client.post("/api/v1/auth/login", json={"identifier": admin.email, "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "export_declaration",
            "taxable_event_id": "EXP-OR-99",
            "base_amount": 100,
            "currency": "MGA",
        },
    )
    assert created.status_code == 201
    tax_id = created.json()["records"][0]["id"]
    patch = client.patch(f"/api/v1/taxes/{tax_id}/status", headers=headers, json={"status": "PAID"})
    assert patch.status_code == 400
    assert patch.json()["detail"]["message"] == "preuve_paiement_obligatoire"


def test_transformation_mass_balance_required(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    raffineur = _create_actor_with_role(db_session, region, district, commune, version, "raffineur@example.com", "raffinerie_operator")
    db_session.add(ActorRole(actor_id=raffineur.id, role="admin", status="active", valid_from=datetime.now(timezone.utc)))
    db_session.commit()

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=10, actor_id=raffineur.id)
    db_session.add(geo)
    db_session.flush()
    lot = Lot(
        filiere="OR",
        product_type="or_brut",
        unit="g",
        quantity=Decimal("20.0"),
        declared_by_actor_id=raffineur.id,
        current_owner_actor_id=raffineur.id,
        status="available",
        declare_geo_point_id=geo.id,
        qr_code="LOT-TRANS-1",
    )
    db_session.add(lot)
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": raffineur.email, "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    facility = client.post(
        "/api/v1/or/transformation-facilities",
        headers=headers,
        json={
            "facility_type": "raffinerie",
            "operator_actor_id": raffineur.id,
            "autorisation_ref": "AUT-RAFF-001",
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_to": "2027-01-01T00:00:00Z",
            "capacity_declared": 1000,
            "status": "active",
        },
    )
    assert facility.status_code == 201

    transform = client.post(
        "/api/v1/or/transformation-events",
        headers=headers,
        json={
            "lot_input_id": lot.id,
            "facility_id": facility.json()["id"],
            "quantity_input": 10,
            "quantity_output": 8,
            "perte_declared": 1,
            "output_product_type": "or_raffine",
            "output_unit": "g",
        },
    )
    assert transform.status_code == 400
    assert transform.json()["detail"]["message"] == "bilan_masse_invalide"


def test_export_checklist_blocks_missing_documents(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "bijoutier-check@example.com", "bijoutier")
    db_session.add(ActorRole(actor_id=actor.id, role="admin", status="active", valid_from=datetime.now(timezone.utc)))
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": actor.email, "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/exports", headers=headers, json={"destination": "Dubai", "total_weight": 4.0})
    assert created.status_code == 201
    export_id = created.json()["id"]

    submitted = client.patch(f"/api/v1/exports/{export_id}/status", headers=headers, json={"status": "submitted"})
    assert submitted.status_code == 200
    blocked = client.patch(f"/api/v1/exports/{export_id}/status", headers=headers, json={"status": "ready_for_control"})
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["message"] == "dossier_incomplet_piece_manquante"


def test_export_checklist_sla_48h_block(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor_with_role(db_session, region, district, commune, version, "bijoutier-sla@example.com", "bijoutier")
    db_session.add(ActorRole(actor_id=actor.id, role="admin", status="active", valid_from=datetime.now(timezone.utc)))
    db_session.commit()

    login = client.post("/api/v1/auth/login", json={"identifier": actor.email, "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/exports", headers=headers, json={"destination": "Paris", "total_weight": 4.0})
    export_id = created.json()["id"]
    client.patch(f"/api/v1/exports/{export_id}/status", headers=headers, json={"status": "submitted"})

    # Force SLA expiration
    items = db_session.query(ExportChecklistItem).filter_by(export_id=export_id).all()
    for item in items:
        item.due_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    blocked = client.patch(f"/api/v1/exports/{export_id}/status", headers=headers, json={"status": "ready_for_control"})
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["message"] == "dossier_incomplet_sla_depasse_48h"
