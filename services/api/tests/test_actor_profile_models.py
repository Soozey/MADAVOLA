from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.territory import Commune, District, Region, TerritoryVersion


def _seed_territory(db_session):
    version = TerritoryVersion(
        version_tag="v-profile",
        source_filename="seed.xlsx",
        checksum_sha256="seed",
        status="active",
        imported_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()
    region = Region(version_id=version.id, code="01", name="Analamanga", name_normalized="analamanga")
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


def _create_actor(db_session, *, email: str, phone: str, role: str, region_id: int, district_id: int, commune_id: int, version_id: int):
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
    db_session.add(ActorRole(actor_id=actor.id, role=role, status="active"))
    db_session.commit()
    return actor


def _auth(client, identifier: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": "secret"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_actor_wallet_and_kyc_endpoints(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    actor = _create_actor(
        db_session,
        email="wallet.kyc@test.mg",
        phone="0348111111",
        role="orpailleur",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    headers = _auth(client, actor.email)

    wallet = client.post(
        f"/api/v1/actors/{actor.id}/wallets",
        headers=headers,
        json={"provider": "mobile_money", "operator_name": "mvola", "account_ref": "0348000000", "is_primary": True},
    )
    assert wallet.status_code == 201
    assert wallet.json()["is_primary"] is True

    wallets = client.get(f"/api/v1/actors/{actor.id}/wallets", headers=headers)
    assert wallets.status_code == 200
    assert len(wallets.json()) == 1

    kyc = client.post(
        f"/api/v1/actors/{actor.id}/kyc",
        headers=headers,
        json={"pieces": ["cin_recto.jpg", "cin_verso.jpg"], "note": "dossier initial"},
    )
    assert kyc.status_code == 201
    assert kyc.json()["pieces"] == ["cin_recto.jpg", "cin_verso.jpg"]

    kycs = client.get(f"/api/v1/actors/{actor.id}/kyc", headers=headers)
    assert kycs.status_code == 200
    assert len(kycs.json()) == 1


def test_commune_profile_patch(client, db_session):
    region, district, commune, version = _seed_territory(db_session)
    agent = _create_actor(
        db_session,
        email="commune.agent@test.mg",
        phone="0348222222",
        role="commune_agent",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        version_id=version.id,
    )
    headers = _auth(client, agent.email)

    patched = client.patch(
        f"/api/v1/actors/communes/{commune.id}/profile",
        headers=headers,
        json={
            "mobile_money_account_ref": "0348999999",
            "receiver_name": "Receveur Commune",
            "receiver_phone": "0348777777",
            "active": True,
        },
    )
    assert patched.status_code == 200
    assert patched.json()["mobile_money_account_ref"] == "0348999999"

    loaded = client.get(f"/api/v1/actors/communes/{commune.id}/profile", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["receiver_name"] == "Receveur Commune"

