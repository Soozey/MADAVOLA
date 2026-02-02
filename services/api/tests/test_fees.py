from datetime import datetime, timezone
from io import BytesIO

import openpyxl

from app.models.actor import Actor
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

    response = client.post(
        "/api/v1/fees",
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
