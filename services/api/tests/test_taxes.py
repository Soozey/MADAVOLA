from datetime import datetime, timezone
from decimal import Decimal

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.payment import PaymentProvider, PaymentRequest
from app.models.tax import TaxRecord
from app.models.tax import TaxEventRegistry
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.taxes.service import compute_dtspm_breakdown
from app.taxes.service import compute_tax_event_breakdown


def _seed_admin(db_session):
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
    actor = Actor(
        type_personne="physique",
        nom="Admin",
        prenoms="System",
        telephone="0349999900",
        email="admin-tax@example.com",
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
    db_session.add(ActorRole(actor_id=actor.id, role="admin", status="active"))
    db_session.commit()
    return actor


def test_dtspm_breakdown_reference_values():
    breakdown = compute_dtspm_breakdown(Decimal("100"), "MGA")
    assert breakdown["dtspm_total_amount"] == Decimal("5.00")
    assert breakdown["redevance"]["amount"] == Decimal("3.00")
    assert breakdown["ristourne"]["amount"] == Decimal("2.00")

    ristourne_lines = {line["beneficiary_level"]: line for line in breakdown["ristourne"]["beneficiaries"]}
    assert ristourne_lines["FNP"]["amount"] == Decimal("0.20")
    assert ristourne_lines["COMMUNE"]["amount"] == Decimal("1.08")
    assert ristourne_lines["REGION"]["amount"] == Decimal("0.54")
    assert ristourne_lines["PROVINCE"]["amount"] == Decimal("0.18")


def test_tax_event_prevents_duplicate_for_same_event_but_allows_new_event(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "taxable_event_type": "export_declaration",
        "taxable_event_id": "EXP-0001",
        "base_amount": 100,
        "currency": "MGA",
    }
    first = client.post("/api/v1/taxes/events", headers=headers, json=payload)
    assert first.status_code == 201
    assert len(first.json()["records"]) == 5

    duplicate = client.post("/api/v1/taxes/events", headers=headers, json=payload)
    assert duplicate.status_code == 409

    second_event = dict(payload)
    second_event["taxable_event_id"] = "EXP-0002"
    second = client.post("/api/v1/taxes/events", headers=headers, json=second_event)
    assert second.status_code == 201
    assert len(second.json()["records"]) == 5

    rows = db_session.query(TaxRecord).all()
    assert len(rows) == 10


def test_local_sale_dtspm_uses_local_market_value(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    local_value = client.post(
        "/api/v1/taxes/local-market-values",
        headers=headers,
        json={
            "filiere": "OR",
            "substance": "OR",
            "unit": "kg",
            "value_per_unit": 500000,
            "currency": "MGA",
            "legal_reference": "Arrete Mines 2026 - valeur marchande locale OR",
            "version_tag": "arr-2026-01",
            "effective_from": "2026-01-01T00:00:00Z",
            "status": "active",
        },
    )
    assert local_value.status_code == 201

    created = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "LOCAL_SALE_DTSPM",
            "taxable_event_id": "LOC-OR-001",
            "assiette_mode": "local_market_value",
            "quantity": 2,
            "unit": "kg",
            "substance": "OR",
            "currency": "MGA",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["breakdown"]["base_amount"] == 1000000.0
    assert body["breakdown"]["dtspm_total_amount"] == 50000.0
    assert body["event"]["invoice_number"].startswith("FAC-")
    assert body["event"]["invoice_document_id"] is not None
    assert len(body["records"]) == 5


def test_dtspm_abatement_only_for_national_refinery_or():
    with_abatement = compute_tax_event_breakdown(
        event_type="EXPORT_DTSPM",
        base_amount=Decimal("100"),
        currency="MGA",
        filiere="OR",
        is_transformed=True,
        transformation_origin="national_refinery",
    )
    assert with_abatement["dtspm_total_amount"] == Decimal("3.50")
    assert with_abatement["redevance"]["amount"] == Decimal("2.10")
    assert with_abatement["ristourne"]["amount"] == Decimal("1.40")

    no_abatement = compute_tax_event_breakdown(
        event_type="EXPORT_DTSPM",
        base_amount=Decimal("100"),
        currency="MGA",
        filiere="OR",
        is_transformed=True,
        transformation_origin="other",
    )
    assert no_abatement["dtspm_total_amount"] == Decimal("5.00")
    assert no_abatement["redevance"]["amount"] == Decimal("3.00")
    assert no_abatement["ristourne"]["amount"] == Decimal("2.00")


def test_tax_event_anti_double_key_blocks_duplicate_tuple(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "EXPORT_DTSPM",
            "taxable_event_id": "EXP-A",
            "base_amount": 1000,
            "currency": "MGA",
            "period_key": "2026-02",
            "reference_transaction": "TX-1",
        },
    )
    assert first.status_code == 201

    duplicate_tuple = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "EXPORT_DTSPM",
            "taxable_event_id": "EXP-B",
            "base_amount": 1000,
            "currency": "MGA",
            "period_key": "2026-02",
            "reference_transaction": "TX-1",
        },
    )
    assert duplicate_tuple.status_code == 409


def test_titrage_poinconnage_split_35_35_30(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "TITRAGE_POINCONNAGE",
            "taxable_event_id": "TIT-001",
            "base_amount": 100,
            "currency": "MGA",
            "assiette_mode": "fixed_amount",
        },
    )
    assert created.status_code == 201
    records = created.json()["records"]
    assert len(records) == 3
    by_level = {row["beneficiary_level"]: row for row in records}
    assert by_level["BUDGET_GENERAL"]["tax_amount"] == 35.0
    assert by_level["BGGLM"]["tax_amount"] == 35.0
    assert by_level["COM"]["tax_amount"] == 30.0


def test_collector_card_right_split_50_30_20(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "DROIT_CARTE_COLLECTEUR",
            "taxable_event_id": "CARD-001",
            "base_amount": 100,
            "currency": "MGA",
            "assiette_mode": "fixed_amount",
        },
    )
    assert created.status_code == 201
    records = created.json()["records"]
    assert len(records) == 3
    by_level = {row["beneficiary_level"]: row for row in records}
    assert by_level["COMMUNE"]["tax_amount"] == 50.0
    assert by_level["REGION"]["tax_amount"] == 30.0
    assert by_level["COM"]["tax_amount"] == 20.0


def test_tax_event_receipt_generated_when_fully_paid(client, db_session):
    admin = _seed_admin(db_session)
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/v1/taxes/events",
        headers=headers,
        json={
            "taxable_event_type": "EXPORT_DTSPM",
            "taxable_event_id": "EXP-PAY-001",
            "base_amount": 1000,
            "currency": "MGA",
        },
    )
    assert created.status_code == 201
    records = created.json()["records"]

    provider = PaymentProvider(code="mvola-tax", name="MVola Tax", enabled=True)
    db_session.add(provider)
    db_session.flush()
    payment = PaymentRequest(
        provider_id=provider.id,
        payer_actor_id=admin.id,
        payee_actor_id=admin.id,
        amount=Decimal("1000"),
        currency="MGA",
        status="success",
        external_ref="tax-paid-001",
    )
    db_session.add(payment)
    db_session.commit()

    for item in records:
        patched = client.patch(
            f"/api/v1/taxes/{item['id']}/status",
            headers=headers,
            json={"status": "PAID", "payment_request_id": payment.id},
        )
        assert patched.status_code == 200

    event = (
        db_session.query(TaxEventRegistry)
        .filter(TaxEventRegistry.taxable_event_type == "EXPORT_DTSPM", TaxEventRegistry.taxable_event_id == "EXP-PAY-001")
        .first()
    )
    assert event is not None
    assert event.status == "PAID"
    assert event.receipt_number is not None
    assert event.receipt_document_id is not None
