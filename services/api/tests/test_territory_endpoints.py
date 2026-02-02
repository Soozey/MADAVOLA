from io import BytesIO

import openpyxl

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


def test_cascade_endpoints(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")

    regions = client.get("/api/v1/territories/regions").json()
    assert regions == [{"code": "01", "name": "Analamanga"}]

    districts = client.get("/api/v1/territories/districts?region_code=01").json()
    assert districts == [
        {"code": "0101", "name": "Antananarivo Renivohitra", "region_code": "01"}
    ]

    communes = client.get("/api/v1/territories/communes?district_code=0101").json()
    assert communes == [
        {
            "code": "010101",
            "name": "Antananarivo I",
            "district_code": "0101",
            "commune_mobile_money_msisdn": None,
        }
    ]

    fokontany = client.get("/api/v1/territories/fokontany?commune_code=010101").json()
    assert fokontany == [
        {"code": "010101-001", "name": "Isotry", "commune_code": "010101"}
    ]

    active = client.get("/api/v1/territories/active").json()
    assert active["version_tag"] == "v1"

    version = client.get("/api/v1/territories/versions/v1").json()
    assert version["version_tag"] == "v1"
