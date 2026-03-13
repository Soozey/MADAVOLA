from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.or_compliance import KaraBolamenaCard
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


def _create_actor(db_session, *, email: str, phone: str, region_id: int, district_id: int, commune_id: int, version_id: int):
    actor = Actor(
        type_personne="physique",
        nom=email.split("@")[0],
        prenoms="Test",
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


def _login(client, email: str) -> str:
    response = client.post("/api/v1/auth/login", json={"identifier": email, "password": "secret"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_karabola_alias_endpoints(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor(
        db_session,
        email="kara.user@example.com",
        phone="0345600001",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    admin = _create_actor(
        db_session,
        email="kara.admin@example.com",
        phone="0345600002",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    target = _create_actor(
        db_session,
        email="kara.target@example.com",
        phone="0345600003",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    db_session.add(ActorRole(actor_id=admin.id, role="admin", status="active", valid_from=datetime.now(timezone.utc)))
    db_session.flush()
    card = KaraBolamenaCard(
        actor_id=actor.id,
        commune_id=commune.id,
        card_uid="MDV-CARD-TEST",
        card_number="MDV-OR-010101-26-000001",
        unique_identifier="KARA-TEST-1",
        status="active",
        nationality="mg",
        cin="101010101010",
        residence_verified=True,
        tax_compliant=True,
        zone_allowed=True,
        public_order_clear=True,
    )
    db_session.add(card)
    db_session.commit()

    user_token = _login(client, actor.email)
    admin_token = _login(client, admin.email)

    listing = client.get("/api/v1/karabola", headers={"Authorization": f"Bearer {user_token}"})
    assert listing.status_code == 200
    assert len(listing.json()) >= 1

    verify = client.post(
        "/api/v1/karabola/verify",
        json={"card_ref": card.card_number},
    )
    assert verify.status_code == 200
    assert verify.json()["card_id"] == card.id

    relink = client.post(
        "/api/v1/karabola/link-user",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"card_type": "kara_bolamena", "card_id": card.id, "actor_id": target.id},
    )
    assert relink.status_code == 200
    db_session.refresh(card)
    assert card.actor_id == target.id
