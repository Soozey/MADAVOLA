from datetime import datetime, timezone
from io import BytesIO

import openpyxl

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.fee import Fee
from app.territories.importer import import_territory_excel


def _build_excel() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "region_code",
            "region_name",
            "district_code",
            "district_name",
            "commune_code",
            "commune_name",
            "fokontany_code",
            "fokontany_name",
        ]
    )
    sheet.append(
        [
            "01",
            "Analamanga",
            "0101",
            "Antananarivo Renivohitra",
            "010101",
            "Antananarivo I",
            "010101-001",
            "Isotry",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_create_fee(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    admin = Actor(
        type_personne="physique",
        nom="Admin",
        prenoms="Root",
        telephone="0340000199",
        email="adminfee@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(admin)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=admin.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=admin.id, role="admin", status="active"))

    actor = Actor(
        type_personne="physique",
        nom="Rakoto",
        prenoms="Jean",
        telephone="0340000100",
        email="rakoto@example.com",
        status="pending",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "secret"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/fees",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fee_type": "account_opening_commune",
            "actor_id": actor.id,
            "commune_id": 1,
            "amount": 10000,
            "currency": "MGA",
        },
    )
    assert response.status_code == 201

    fee = db_session.query(Fee).first()
    assert fee is not None
    assert fee.status == "pending"


def test_fee_list_rbac(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    owner = Actor(
        type_personne="physique",
        nom="Owner",
        prenoms="Fee",
        telephone="0340000200",
        email="ownerfee@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    other = Actor(
        type_personne="physique",
        nom="Other",
        prenoms="Fee",
        telephone="0340000201",
        email="otherfee@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([owner, other])
    db_session.flush()
    db_session.add(ActorAuth(actor_id=other.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(
        Fee(
            fee_type="account_opening_commune",
            actor_id=owner.id,
            commune_id=1,
            amount=10000,
            currency="MGA",
            status="pending",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": other.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/fees",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_fee_get_rbac(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    owner = Actor(
        type_personne="physique",
        nom="Owner2",
        prenoms="Fee",
        telephone="0340000300",
        email="owner2fee@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    other = Actor(
        type_personne="physique",
        nom="Other2",
        prenoms="Fee",
        telephone="0340000301",
        email="other2fee@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([owner, other])
    db_session.flush()
    db_session.add(ActorAuth(actor_id=other.id, password_hash=hash_password("secret"), is_active=1))
    fee = Fee(
        fee_type="account_opening_commune",
        actor_id=owner.id,
        commune_id=1,
        amount=10000,
        currency="MGA",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(fee)
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": other.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    denied = client.get(
        f"/api/v1/fees/{fee.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 400
