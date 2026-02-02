from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
from app.models.fee import Fee
from app.models.payment import PaymentProvider, PaymentRequest, WebhookInbox
from app.models.territory import Commune, District, Region, TerritoryVersion


def _create_actor(db_session, email: str, phone: str, region_id: int, district_id: int, commune_id: int, version_id: int):
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone=phone,
        email=email,
        status="active",
        region_id=region_id,
        district_id=district_id,
        commune_id=commune_id,
        territory_version_id=version_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()
    return actor


def test_payment_initiate_and_webhook_idempotent(client, db_session):
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

    provider = PaymentProvider(code="mvola", name="mVola", enabled=True)
    db_session.add(provider)
    db_session.commit()
    payer = _create_actor(
        db_session, "payer@example.com", "0340000009", region.id, district.id, commune.id, version.id
    )
    payee = _create_actor(
        db_session, "payee@example.com", "0340000010", region.id, district.id, commune.id, version.id
    )

    fee = Fee(
        fee_type="account_opening_commune",
        actor_id=payer.id,
        commune_id=commune.id,
        amount=10000,
        currency="MGA",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(fee)
    db_session.commit()

    response = client.post(
        "/api/v1/payments/initiate",
        json={
            "provider_code": "mvola",
            "payer_actor_id": payer.id,
            "payee_actor_id": payee.id,
            "fee_id": fee.id,
            "amount": 10000,
            "currency": "MGA",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "pending"

    webhook = client.post(
        "/api/v1/payments/webhooks/mvola",
        json={"external_ref": payload["external_ref"], "status": "success"},
    )
    assert webhook.status_code == 200

    duplicate = client.post(
        "/api/v1/payments/webhooks/mvola",
        json={"external_ref": payload["external_ref"], "status": "success"},
    )
    assert duplicate.json()["idempotent"] is True

    inbox_count = (
        db_session.query(WebhookInbox)
        .filter_by(external_ref=payload["external_ref"])
        .count()
    )
    assert inbox_count == 1

    request = (
        db_session.query(PaymentRequest).filter_by(external_ref=payload["external_ref"]).first()
    )
    assert request.status == "success"
    db_session.refresh(fee)
    assert fee.status == "paid"
