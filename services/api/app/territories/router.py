from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.common.errors import bad_request
from app.core.config import settings
from app.db import get_db
from app.models.territory import Commune, District, Fokontany, Region, TerritoryVersion
from app.territories.importer import import_territory_excel
from app.territories.schemas import (
    CommuneOut,
    DistrictOut,
    FokontanyOut,
    RegionOut,
    TerritoryImportResult,
    TerritoryVersionOut,
)

router = APIRouter(prefix=f"{settings.api_prefix}/territories", tags=["territories"])


@router.post("/import", response_model=TerritoryImportResult)
def import_territory(version_tag: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise bad_request("fichier_obligatoire")
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise bad_request("format_fichier_invalide", {"expected": "xlsx/xlsm"})
    contents = file.file.read()
    counts = import_territory_excel(db, contents, file.filename, version_tag)
    return TerritoryImportResult(
        version_tag=version_tag,
        regions=counts.regions,
        districts=counts.districts,
        communes=counts.communes,
        fokontany=counts.fokontany,
    )


@router.get("/versions", response_model=list[TerritoryVersionOut])
def list_versions(db: Session = Depends(get_db)):
    versions = (
        db.query(TerritoryVersion)
        .order_by(TerritoryVersion.imported_at.desc())
        .all()
    )
    return [
        TerritoryVersionOut(
            version_tag=v.version_tag,
            source_filename=v.source_filename,
            checksum_sha256=v.checksum_sha256,
            status=v.status,
            imported_at=v.imported_at,
            activated_at=v.activated_at,
        )
        for v in versions
    ]


@router.get("/versions/{version_tag}", response_model=TerritoryVersionOut)
def get_version(version_tag: str, db: Session = Depends(get_db)):
    version = db.query(TerritoryVersion).filter_by(version_tag=version_tag).first()
    if not version:
        raise bad_request("version_introuvable")
    return TerritoryVersionOut(
        version_tag=version.version_tag,
        source_filename=version.source_filename,
        checksum_sha256=version.checksum_sha256,
        status=version.status,
        imported_at=version.imported_at,
        activated_at=version.activated_at,
    )


@router.get("/active", response_model=TerritoryVersionOut)
def get_active_version(db: Session = Depends(get_db)):
    version = _get_active_version(db)
    return TerritoryVersionOut(
        version_tag=version.version_tag,
        source_filename=version.source_filename,
        checksum_sha256=version.checksum_sha256,
        status=version.status,
        imported_at=version.imported_at,
        activated_at=version.activated_at,
    )


@router.get("/regions", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)):
    active = _get_active_version(db)
    regions = (
        db.query(Region)
        .filter(Region.version_id == active.id)
        .order_by(Region.name.asc())
        .all()
    )
    return [RegionOut(code=r.code, name=r.name) for r in regions]


@router.get("/districts", response_model=list[DistrictOut])
def list_districts(region_code: str, db: Session = Depends(get_db)):
    active = _get_active_version(db)
    region = (
        db.query(Region)
        .filter(Region.version_id == active.id, Region.code == region_code)
        .first()
    )
    if not region:
        return []
    districts = (
        db.query(District)
        .filter(District.version_id == active.id, District.region_id == region.id)
        .order_by(District.name.asc())
        .all()
    )
    return [
        DistrictOut(code=d.code, name=d.name, region_code=region_code) for d in districts
    ]


@router.get("/communes", response_model=list[CommuneOut])
def list_communes(district_code: str, db: Session = Depends(get_db)):
    active = _get_active_version(db)
    district = (
        db.query(District)
        .filter(District.version_id == active.id, District.code == district_code)
        .first()
    )
    if not district:
        return []
    communes = (
        db.query(Commune)
        .filter(Commune.version_id == active.id, Commune.district_id == district.id)
        .order_by(Commune.name.asc())
        .all()
    )
    return [
        CommuneOut(
            code=c.code,
            name=c.name,
            district_code=district_code,
            commune_mobile_money_msisdn=c.mobile_money_msisdn,
        )
        for c in communes
    ]


@router.get("/fokontany", response_model=list[FokontanyOut])
def list_fokontany(commune_code: str, db: Session = Depends(get_db)):
    active = _get_active_version(db)
    commune = (
        db.query(Commune)
        .filter(Commune.version_id == active.id, Commune.code == commune_code)
        .first()
    )
    if not commune:
        return []
    fokontany = (
        db.query(Fokontany)
        .filter(Fokontany.version_id == active.id, Fokontany.commune_id == commune.id)
        .order_by(Fokontany.name.asc())
        .all()
    )
    return [
        FokontanyOut(code=f.code, name=f.name, commune_code=commune_code) for f in fokontany
    ]


def _get_active_version(db: Session) -> TerritoryVersion:
    version = db.query(TerritoryVersion).filter_by(status="active").first()
    if not version:
        raise bad_request("territoire_non_charge")
    return version
