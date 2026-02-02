from datetime import datetime, timezone
from io import BytesIO

from app.models.actor import Actor
from app.models.document import Document
from app.models.territory import Commune, District, Region, TerritoryVersion


def _seed_territory(db_session):
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
    db_session.commit()
    return region, district, commune, version


def test_upload_document(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Doc",
        prenoms="Owner",
        telephone="0340003000",
        email="doc@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.commit()

    file_content = b"test-file"
    response = client.post(
        "/api/v1/documents",
        data={
            "doc_type": "facture",
            "owner_actor_id": str(actor.id),
            "related_entity_type": "invoice",
            "related_entity_id": "INV-0001",
        },
        files={"file": ("invoice.txt", BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 201
    doc = db_session.query(Document).first()
    assert doc is not None
