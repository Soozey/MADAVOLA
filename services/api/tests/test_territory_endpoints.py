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
    assert len(regions) == 1
    assert regions[0]["code"] == "01"
    assert regions[0]["name"] == "Analamanga"

    districts = client.get("/api/v1/territories/districts?region_code=01").json()
    assert len(districts) == 1
    assert districts[0]["code"] == "0101"
    assert districts[0]["name"] == "Antananarivo Renivohitra"
    assert districts[0]["region_code"] == "01"

    communes = client.get("/api/v1/territories/communes?district_code=0101").json()
    assert len(communes) == 1
    assert communes[0]["code"] == "010101"
    assert communes[0]["name"] == "Antananarivo I"
    assert communes[0]["district_code"] == "0101"
    assert communes[0]["commune_mobile_money_msisdn"] is None

    fokontany = client.get("/api/v1/territories/fokontany?commune_code=010101").json()
    assert len(fokontany) == 1
    assert fokontany[0]["code"] == "010101-001"
    assert fokontany[0]["name"] == "Isotry"
    assert fokontany[0]["commune_code"] == "010101"

    active = client.get("/api/v1/territories/active").json()
    assert active["version_tag"] == "v1"

    version = client.get("/api/v1/territories/versions/v1").json()
    assert version["version_tag"] == "v1"
