from datetime import datetime, timezone
from decimal import Decimal

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.tax import TaxRecord
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.taxes.service import compute_dtspm_breakdown


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
