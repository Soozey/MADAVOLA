from io import BytesIO

import openpyxl
from fastapi import HTTPException

from app.models.territory import TerritoryVersion
from app.territories.importer import import_territory_excel


def _build_excel(rows: list[dict]) -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    headers = [
        "region_code",
        "region_name",
        "district_code",
        "district_name",
        "commune_code",
        "commune_name",
        "fokontany_code",
        "fokontany_name",
        "commune_mobile_money_msisdn",
    ]
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(h) for h in headers])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_import_territory_creates_version(db_session):
    content = _build_excel(
        [
            {
                "region_code": "01",
                "region_name": "Analamanga",
                "district_code": "0101",
                "district_name": "Antananarivo Renivohitra",
                "commune_code": "010101",
                "commune_name": "Antananarivo I",
                "fokontany_code": "010101-001",
                "fokontany_name": "Isotry",
                "commune_mobile_money_msisdn": "0340000000",
            }
        ]
    )
    counts = import_territory_excel(db_session, content, "territory.xlsx", "v1")
    assert counts.regions == 1
    assert counts.districts == 1
    assert counts.communes == 1
    assert counts.fokontany == 1

    version = db_session.query(TerritoryVersion).filter_by(version_tag="v1").first()
    assert version is not None
    assert version.status == "active"


def test_import_rejects_missing_columns(db_session):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["region_code"])
    sheet.append(["01"])
    buffer = BytesIO()
    workbook.save(buffer)

    try:
        import_territory_excel(db_session, buffer.getvalue(), "bad.xlsx", "v2")
        assert False, "expected error"
    except HTTPException as exc:
        assert exc.detail["message"] == "colonnes_requises_manquantes"
