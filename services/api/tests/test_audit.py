from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth
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


def test_list_audit_logs(client, db_session):
    import_territory_excel(db_session, _build_excel(), "territory.xlsx", "v1")
    actor = Actor(
        type_personne="physique",
        nom="Auditor",
        prenoms="Test",
        telephone="0340000600",
        email="audit@example.com",
        status="active",
        region_id=1,
        district_id=1,
        commune_id=1,
        territory_version_id=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(
        AuditLog(
            actor_id=actor.id,
            action="login",
            entity_type="auth",
            entity_id="1",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": actor.email, "password": "secret"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1
