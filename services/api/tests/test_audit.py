from datetime import datetime, timezone

from app.models.actor import Actor
from app.models.audit import AuditLog
from app.models.territory import Commune, District, Region, TerritoryVersion
from app.territories.importer import import_territory_excel
from io import BytesIO
import openpyxl


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


def test_audit_log_on_actor_create(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    geo = client.post(
        "/api/v1/geo-points",
        json={"lat": -18.91, "lon": 47.52, "accuracy_m": 12, "source": "gps"},
    ).json()

    response = client.post(
        "/api/v1/actors",
        json={
            "type_personne": "physique",
            "nom": "Rakoto",
            "prenoms": "Jean",
            "telephone": "0340000111",
            "password": "secret",
            "region_code": "01",
            "district_code": "0101",
            "commune_code": "010101",
            "fokontany_code": "010101-001",
            "geo_point_id": geo["id"],
            "roles": ["orpailleur"],
        },
    )
    assert response.status_code == 201

    audit = db_session.query(AuditLog).filter_by(action="actor_created").first()
    assert audit is not None
