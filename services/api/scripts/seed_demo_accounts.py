#!/usr/bin/env python3
"""
Seed de demonstration MADAVOLA:
- 1 compte par role RBAC
- comptes territoriaux (region/district/commune)
- forçage changement de mot de passe au premier login
- compte admin multi-role pour demo (switch role sans recreer de compte)

Usage:
  python services/api/scripts/seed_demo_accounts.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


_api_root = os.environ.get("API_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

from app.audit.logger import write_audit
from app.auth.roles_config import ROLE_DEFINITIONS
from app.auth.security import hash_password
from app.db import SessionLocal
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.actor_filiere import ActorFiliere
from app.models.fee import Fee
from app.models.geo import GeoPoint
from app.models.territory import Commune, District, Region, TerritoryVersion


DEFAULT_PASSWORD = "admin123"
DEFAULT_DOMAIN = "madavola.mg"
DEFAULT_LAT = -18.8792
DEFAULT_LON = 47.5079
OPENING_FEE_ROLES = {"orpailleur", "collecteur", "comptoir", "comptoir_operator"}
MULTI_ROLE_ADMIN_EMAIL = "admin@madavola.mg"

# Mapping demandé par le métier (roles techniques existants conservés)
ROLE_EMAIL_OVERRIDES = {
    "admin": "admin@madavola.mg",
    "pr": "president@madavola.mg",
    "mmrs": "mines@madavola.mg",
    "mef": "finances@madavola.mg",
    "dgd": "douane@madavola.mg",
    "forets": "environnement@madavola.mg",
    "com": "com@madavola.mg",
    "region": "analamanga@madavola.mg",
    "district_agent": "antananarivo-atsimondrano@madavola.mg",
    "commune_agent": "antanambaobe@madavola.mg",
    "orpailleur": "orpailleur1@madavola.mg",
    "collecteur": "collecteur1@madavola.mg",
    "comptoir_operator": "comptoir1@madavola.mg",
    "pierre_lapidaire": "lapidaire1@madavola.mg",
    "pierre_exportateur": "exportateur-pierre@madavola.mg",
    "bois_exploitant": "exploitant-bois@madavola.mg",
    "bois_transformateur": "transformateur-bois@madavola.mg",
    "bois_exportateur": "exportateur-bois@madavola.mg",
    "transporteur": "transporteur1@madavola.mg",
    "bijoutier": "bijoutier1@madavola.mg",
    "fnp": "public@madavola.mg",
}


@dataclass
class AccountSpec:
    email: str
    role: str
    nom: str
    region_id: int
    district_id: int
    commune_id: int
    territory_version_id: int
    filieres: tuple[str, ...]
    type_personne: str = "personne_morale"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only.lower()).strip("-")
    return slug or "acteur"


def filieres_for_role(role: str) -> tuple[str, ...]:
    if role.startswith("pierre_"):
        return ("PIERRE",)
    if role.startswith("bois_"):
        return ("BOIS",)
    return ("OR",)


def role_default_name(role: str) -> str:
    definition = ROLE_DEFINITIONS.get(role, {})
    institution = (definition.get("institution") or role).strip()
    return institution if institution else role.replace("_", " ").title()


def ensure_active_territory(db) -> tuple[TerritoryVersion, Region, District, Commune]:
    version = db.query(TerritoryVersion).filter(TerritoryVersion.status == "active").first()
    if not version:
        now = datetime.now(timezone.utc)
        version = TerritoryVersion(
            version_tag="demo-auto",
            source_filename="auto",
            checksum_sha256="demo-auto",
            status="active",
            imported_at=now,
            activated_at=now,
        )
        db.add(version)
        db.flush()
        region = Region(version_id=version.id, code="DEFAULT", name="Region Demo", name_normalized="region demo")
        db.add(region)
        db.flush()
        district = District(
            version_id=version.id,
            region_id=region.id,
            code="DEFAULT",
            name="District Demo",
            name_normalized="district demo",
        )
        db.add(district)
        db.flush()
        commune = Commune(
            version_id=version.id,
            district_id=district.id,
            code="DEFAULT",
            name="Commune Demo",
            name_normalized="commune demo",
        )
        db.add(commune)
        db.commit()
        return version, region, district, commune

    region = db.query(Region).filter(Region.version_id == version.id).order_by(Region.id.asc()).first()
    if not region:
        raise RuntimeError("Aucune region disponible dans la version active")
    district = (
        db.query(District)
        .filter(District.version_id == version.id, District.region_id == region.id)
        .order_by(District.id.asc())
        .first()
    )
    if not district:
        raise RuntimeError("Aucun district disponible dans la version active")
    commune = (
        db.query(Commune)
        .filter(Commune.version_id == version.id, Commune.district_id == district.id)
        .order_by(Commune.id.asc())
        .first()
    )
    if not commune:
        raise RuntimeError("Aucune commune disponible dans la version active")
    return version, region, district, commune


def all_regions(db, version_id: int) -> list[Region]:
    return db.query(Region).filter(Region.version_id == version_id).order_by(Region.id.asc()).all()


def all_districts(db, version_id: int) -> list[District]:
    return db.query(District).filter(District.version_id == version_id).order_by(District.id.asc()).all()


def all_communes(db, version_id: int) -> list[Commune]:
    return db.query(Commune).filter(Commune.version_id == version_id).order_by(Commune.id.asc()).all()


def build_phone_generator(existing_values: Iterable[str]):
    used = {v for v in existing_values if v}
    counter = 1

    def _next() -> str:
        nonlocal counter
        while True:
            candidate = f"+26134{counter:06d}"
            counter += 1
            if candidate in used:
                continue
            used.add(candidate)
            return candidate

    return _next


def ensure_geo_point(db, lat: float, lon: float) -> GeoPoint:
    point = GeoPoint(lat=lat, lon=lon, accuracy_m=25, source="seed_demo_accounts")
    db.add(point)
    db.flush()
    return point


def ensure_role(db, actor_id: int, role: str, now: datetime) -> None:
    row = (
        db.query(ActorRole)
        .filter(ActorRole.actor_id == actor_id, ActorRole.role == role)
        .order_by(ActorRole.id.desc())
        .first()
    )
    if row:
        row.status = "active"
        row.valid_from = row.valid_from or now
        row.valid_to = None
        return
    db.add(
        ActorRole(
            actor_id=actor_id,
            role=role,
            status="active",
            valid_from=now,
            valid_to=None,
        )
    )


def ensure_filieres(db, actor_id: int, filieres: Iterable[str]) -> None:
    existing = {
        row[0]
        for row in db.query(ActorFiliere.filiere).filter(ActorFiliere.actor_id == actor_id).all()
        if row[0]
    }
    for filiere in filieres:
        if filiere in existing:
            continue
        db.add(ActorFiliere(actor_id=actor_id, filiere=filiere))


def ensure_opening_fee_paid(db, actor_id: int, commune_id: int, role: str) -> None:
    if role not in OPENING_FEE_ROLES:
        return
    fee = (
        db.query(Fee)
        .filter(Fee.actor_id == actor_id, Fee.fee_type == "account_opening_commune")
        .order_by(Fee.id.desc())
        .first()
    )
    if not fee:
        fee = Fee(
            fee_type="account_opening_commune",
            actor_id=actor_id,
            commune_id=commune_id,
            amount=10000,
            currency="MGA",
            status="pending",
        )
        db.add(fee)
        db.flush()
    if fee.status != "paid":
        fee.status = "paid"
        fee.paid_at = datetime.now(timezone.utc)


def ensure_account(db, spec: AccountSpec, phone_factory, validator_actor_id: int | None) -> tuple[Actor, bool]:
    now = datetime.now(timezone.utc)
    actor = db.query(Actor).filter(Actor.email == spec.email).first()
    created = False

    auth: ActorAuth | None = None

    if not actor:
        geo = ensure_geo_point(db, DEFAULT_LAT, DEFAULT_LON)
        actor = Actor(
            type_personne=spec.type_personne,
            nom=spec.nom,
            prenoms="",
            telephone=phone_factory(),
            email=spec.email,
            region_id=spec.region_id,
            district_id=spec.district_id,
            commune_id=spec.commune_id,
            territory_version_id=spec.territory_version_id,
            signup_geo_point_id=geo.id,
            status="pending",
            created_at=now,
        )
        db.add(actor)
        db.flush()
        db.add(
            ActorAuth(
                actor_id=actor.id,
                password_hash=hash_password(DEFAULT_PASSWORD),
                is_active=1,
                must_change_password=1,
                password_changed_at=None,
                last_login_at=None,
            )
        )
        db.flush()
        auth = db.query(ActorAuth).filter(ActorAuth.actor_id == actor.id).first()
        created = True
        write_audit(
            db,
            actor_id=validator_actor_id,
            action="actor_created",
            entity_type="actor",
            entity_id=str(actor.id),
            meta={"seed_demo": True, "email": spec.email, "role": spec.role},
        )
    else:
        actor.type_personne = spec.type_personne
        actor.nom = actor.nom or spec.nom
        actor.region_id = spec.region_id
        actor.district_id = spec.district_id
        actor.commune_id = spec.commune_id
        actor.territory_version_id = spec.territory_version_id
        if not actor.telephone:
            actor.telephone = phone_factory()
        if not actor.signup_geo_point_id:
            geo = ensure_geo_point(db, DEFAULT_LAT, DEFAULT_LON)
            actor.signup_geo_point_id = geo.id

    if auth is None:
        auth = db.query(ActorAuth).filter(ActorAuth.actor_id == actor.id).first()
    if not auth:
        auth = ActorAuth(
            actor_id=actor.id,
            password_hash=hash_password(DEFAULT_PASSWORD),
            is_active=1,
            must_change_password=1,
            password_changed_at=None,
            last_login_at=None,
        )
        db.add(auth)
    else:
        auth.password_hash = hash_password(DEFAULT_PASSWORD)
        auth.is_active = 1
        auth.must_change_password = 1
        auth.password_changed_at = None
        auth.last_login_at = None

    ensure_role(db, actor.id, spec.role, now)
    ensure_filieres(db, actor.id, spec.filieres)
    ensure_opening_fee_paid(db, actor.id, spec.commune_id, spec.role)

    previous_status = actor.status
    actor.status = "active"
    write_audit(
        db,
        actor_id=validator_actor_id,
        action="actor_status_updated",
        entity_type="actor",
        entity_id=str(actor.id),
        meta={
            "seed_demo": True,
            "old_status": previous_status,
            "new_status": "active",
        },
    )
    write_audit(
        db,
        actor_id=validator_actor_id,
        action="password_policy_enforced",
        entity_type="actor_auth",
        entity_id=str(actor.id),
        meta={
            "seed_demo": True,
            "must_change_password": True,
            "default_password": "admin123",
        },
    )
    return actor, created


def build_role_specs(version: TerritoryVersion, region: Region, district: District, commune: Commune) -> list[AccountSpec]:
    specs: list[AccountSpec] = []
    for role in sorted(ROLE_DEFINITIONS.keys()):
        email = ROLE_EMAIL_OVERRIDES.get(role, f"{slugify(role)}@{DEFAULT_DOMAIN}")
        type_personne = "personne_physique" if role in {"orpailleur", "collecteur", "bijoutier", "transporteur"} else "personne_morale"
        specs.append(
            AccountSpec(
                email=email,
                role=role,
                nom=role_default_name(role),
                region_id=region.id,
                district_id=district.id,
                commune_id=commune.id,
                territory_version_id=version.id,
                filieres=filieres_for_role(role),
                type_personne=type_personne,
            )
        )
    return specs


def build_territory_specs(db, version: TerritoryVersion, fallback_district: District, fallback_commune: Commune) -> list[AccountSpec]:
    specs: list[AccountSpec] = []
    for row in all_regions(db, version.id):
        district = (
            db.query(District)
            .filter(District.version_id == version.id, District.region_id == row.id)
            .order_by(District.id.asc())
            .first()
        ) or fallback_district
        commune = (
            db.query(Commune)
            .filter(Commune.version_id == version.id, Commune.district_id == district.id)
            .order_by(Commune.id.asc())
            .first()
        ) or fallback_commune
        specs.append(
            AccountSpec(
                email=f"{slugify(row.name)}@{DEFAULT_DOMAIN}",
                role="region",
                nom=f"Region {row.name}",
                region_id=row.id,
                district_id=district.id,
                commune_id=commune.id,
                territory_version_id=version.id,
                filieres=("OR",),
                type_personne="personne_morale",
            )
        )

    district_rows = all_districts(db, version.id)
    for row in district_rows:
        commune = (
            db.query(Commune)
            .filter(Commune.version_id == version.id, Commune.district_id == row.id)
            .order_by(Commune.id.asc())
            .first()
        ) or fallback_commune
        specs.append(
            AccountSpec(
                email=f"{slugify(row.name)}@{DEFAULT_DOMAIN}",
                role="district_agent",
                nom=f"District {row.name}",
                region_id=row.region_id,
                district_id=row.id,
                commune_id=commune.id,
                territory_version_id=version.id,
                filieres=("OR",),
                type_personne="personne_morale",
            )
        )

    for row in all_communes(db, version.id):
        district = db.query(District).filter(District.id == row.district_id).first() or fallback_district
        specs.append(
            AccountSpec(
                email=f"{slugify(row.name)}@{DEFAULT_DOMAIN}",
                role="commune_agent",
                nom=f"Commune {row.name}",
                region_id=district.region_id,
                district_id=district.id,
                commune_id=row.id,
                territory_version_id=version.id,
                filieres=("OR",),
                type_personne="personne_morale",
            )
        )
    return specs


def merge_specs(specs: list[AccountSpec]) -> list[AccountSpec]:
    by_email: dict[str, AccountSpec] = {}
    for spec in specs:
        key = spec.email.strip().lower()
        if key not in by_email:
            by_email[key] = spec
            continue
        # Si l'email existe deja, on conserve la premiere spec (priorite métier explicite).
    return list(by_email.values())


def ensure_multi_role_admin(db, admin_actor: Actor) -> None:
    now = datetime.now(timezone.utc)
    for role in ROLE_DEFINITIONS.keys():
        ensure_role(db, admin_actor.id, role, now)
    ensure_filieres(db, admin_actor.id, ("OR", "PIERRE", "BOIS"))
    write_audit(
        db,
        actor_id=admin_actor.id,
        action="multi_role_demo_enabled",
        entity_type="actor",
        entity_id=str(admin_actor.id),
        meta={"roles_count": len(ROLE_DEFINITIONS)},
    )


def main() -> int:
    db = SessionLocal()
    created_count = 0
    updated_count = 0
    rows_for_export: list[dict[str, str]] = []
    try:
        version, default_region, default_district, default_commune = ensure_active_territory(db)

        existing_phones = [row[0] for row in db.query(Actor.telephone).all()]
        next_phone = build_phone_generator(existing_phones)

        role_specs = build_role_specs(version, default_region, default_district, default_commune)
        territory_specs = build_territory_specs(db, version, default_district, default_commune)
        final_specs = merge_specs(role_specs + territory_specs)

        admin_spec = next((s for s in final_specs if s.email.lower() == MULTI_ROLE_ADMIN_EMAIL), None)
        if not admin_spec:
            admin_spec = AccountSpec(
                email=MULTI_ROLE_ADMIN_EMAIL,
                role="admin",
                nom="MADAVOLA",
                region_id=default_region.id,
                district_id=default_district.id,
                commune_id=default_commune.id,
                territory_version_id=version.id,
                filieres=("OR",),
                type_personne="personne_morale",
            )
            final_specs.insert(0, admin_spec)

        admin_actor, admin_created = ensure_account(db, admin_spec, next_phone, validator_actor_id=None)
        if admin_created:
            created_count += 1
        else:
            updated_count += 1
        rows_for_export.append(
            {
                "email": admin_actor.email or "",
                "role": "admin",
                "actor_id": str(admin_actor.id),
                "status": admin_actor.status or "",
                "must_change_password": str(bool(admin_actor.auth.must_change_password if admin_actor.auth else True)),
                "region_id": str(admin_actor.region_id or ""),
                "district_id": str(admin_actor.district_id or ""),
                "commune_id": str(admin_actor.commune_id or ""),
            }
        )
        db.commit()

        for spec in final_specs:
            if spec.email.lower() == MULTI_ROLE_ADMIN_EMAIL:
                continue
            actor, created = ensure_account(db, spec, next_phone, validator_actor_id=admin_actor.id)
            if created:
                created_count += 1
            else:
                updated_count += 1
            rows_for_export.append(
                {
                    "email": actor.email or "",
                    "role": spec.role,
                    "actor_id": str(actor.id),
                    "status": actor.status or "",
                    "must_change_password": str(bool(actor.auth.must_change_password if actor.auth else True)),
                    "region_id": str(actor.region_id or ""),
                    "district_id": str(actor.district_id or ""),
                    "commune_id": str(actor.commune_id or ""),
                }
            )

        ensure_multi_role_admin(db, admin_actor)
        db.commit()

        export_dir = Path("exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"demo_accounts_{datetime.now().date().isoformat()}.csv"
        rows_for_export.sort(key=lambda item: (item["role"], item["email"]))
        with export_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "email",
                    "role",
                    "actor_id",
                    "status",
                    "must_change_password",
                    "region_id",
                    "district_id",
                    "commune_id",
                ],
            )
            writer.writeheader()
            writer.writerows(rows_for_export)

        print("Seed demo accounts: OK")
        print(f"Created: {created_count}")
        print(f"Updated: {updated_count}")
        print(f"Export: {export_path}")
        print(f"Admin multi-role: {MULTI_ROLE_ADMIN_EMAIL}")
        print("Default password (all demo accounts): admin123")
        print("First login password change: REQUIRED")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seed demo accounts failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
