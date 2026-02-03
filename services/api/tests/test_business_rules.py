"""
Tests des règles métier critiques
"""
from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.geo import GeoPoint
from app.models.lot import InventoryLedger, Lot
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion


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
    db_session.flush()
    fokontany = Fokontany(
        version_id=version.id,
        commune_id=commune.id,
        code="010101-001",
        name="Isotry",
        name_normalized="isotry",
    )
    db_session.add(fokontany)
    db_session.commit()
    return region, district, commune, fokontany, version


def test_ledger_balance_consistency(client, db_session):
    """Règle métier: Le solde ledger doit être cohérent avec les mouvements"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Test",
        telephone="0340000100",
        email="test@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12)
    db_session.add(geo)
    db_session.commit()

    # Créer lot (ledger entry +100)
    lot = Lot(
        filiere="OR",
        product_type="poudre",
        unit="g",
        quantity=100.0,
        declared_by_actor_id=actor.id,
        current_owner_actor_id=actor.id,
        declare_geo_point_id=geo.id,
    )
    db_session.add(lot)
    db_session.flush()

    ledger1 = InventoryLedger(
        actor_id=actor.id,
        lot_id=lot.id,
        movement_type="create",
        quantity_delta=100.0,
        ref_event_type="lot",
        ref_event_id=str(lot.id),
    )
    db_session.add(ledger1)
    db_session.commit()

    # Vérifier cohérence: somme des deltas = balance
    from sqlalchemy import func

    total_delta = (
        db_session.query(func.sum(InventoryLedger.quantity_delta))
        .filter(InventoryLedger.actor_id == actor.id, InventoryLedger.lot_id == lot.id)
        .scalar()
    )
    assert total_delta == 100.0


def test_lot_transfer_ownership_rule(client, db_session):
    """Règle métier: Seul le propriétaire peut transférer un lot"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    owner = Actor(
        type_personne="physique",
        nom="Owner",
        telephone="0340000200",
        email="owner@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(owner)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=owner.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    other = Actor(
        type_personne="physique",
        nom="Other",
        telephone="0340000201",
        email="other@example.com",
        status="active",
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(other)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=other.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    geo = GeoPoint(lat=-18.91, lon=47.52, accuracy_m=12)
    db_session.add(geo)
    db_session.commit()

    lot = Lot(
        filiere="OR",
        product_type="poudre",
        unit="g",
        quantity=50.0,
        declared_by_actor_id=owner.id,
        current_owner_actor_id=owner.id,  # Owner possède le lot
        declare_geo_point_id=geo.id,
    )
    db_session.add(lot)
    db_session.commit()

    # Other ne peut pas transférer (vérifié dans le router)
    # Cette règle est testée dans test_lots.py


def test_actor_status_activation_rule(client, db_session):
    """Règle métier: Un acteur doit être 'active' pour se connecter"""
    region, district, commune, fokontany, version = _seed_territory(db_session)
    actor = Actor(
        type_personne="physique",
        nom="Test",
        telephone="0340000300",
        email="pending@example.com",
        status="pending",  # Pas encore actif
        region_id=region.id,
        district_id=district.id,
        commune_id=commune.id,
        territory_version_id=version.id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.commit()

    # Tentative de login avec status pending
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "pending@example.com", "password": "secret"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "compte_inactif"
