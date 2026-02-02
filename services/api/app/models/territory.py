from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


class TerritoryVersion(Base):
    __tablename__ = "territory_versions"

    id = Column(Integer, primary_key=True)
    version_tag = Column(String(50), nullable=False, unique=True)
    source_filename = Column(String(255), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="importing")
    imported_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    activated_at = Column(DateTime(timezone=True))

    regions = relationship("Region", back_populates="version")


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("territory_versions.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(150), nullable=False)
    name_normalized = Column(String(150), nullable=False)

    version = relationship("TerritoryVersion", back_populates="regions")
    districts = relationship("District", back_populates="region")

    __table_args__ = (
        UniqueConstraint("version_id", "code", name="uq_regions_version_code"),
        UniqueConstraint("version_id", "name_normalized", name="uq_regions_version_name"),
    )


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("territory_versions.id"), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(150), nullable=False)
    name_normalized = Column(String(150), nullable=False)

    region = relationship("Region", back_populates="districts")
    communes = relationship("Commune", back_populates="district")

    __table_args__ = (
        UniqueConstraint("version_id", "region_id", "code", name="uq_districts_version_region_code"),
        UniqueConstraint(
            "version_id", "region_id", "name_normalized", name="uq_districts_version_region_name"
        ),
        Index("ix_districts_version_region", "version_id", "region_id"),
    )


class Commune(Base):
    __tablename__ = "communes"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("territory_versions.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    code = Column(String(32), nullable=False)
    name = Column(String(150), nullable=False)
    name_normalized = Column(String(150), nullable=False)
    mobile_money_msisdn = Column(String(32))
    latitude = Column(String(30))
    longitude = Column(String(30))

    district = relationship("District", back_populates="communes")
    fokontany = relationship("Fokontany", back_populates="commune")

    __table_args__ = (
        UniqueConstraint("version_id", "district_id", "code", name="uq_communes_version_district_code"),
        UniqueConstraint(
            "version_id", "district_id", "name_normalized", name="uq_communes_version_district_name"
        ),
        Index("ix_communes_version_district", "version_id", "district_id"),
    )


class Fokontany(Base):
    __tablename__ = "fokontany"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("territory_versions.id"), nullable=False)
    commune_id = Column(Integer, ForeignKey("communes.id"), nullable=False)
    code = Column(String(64))
    name = Column(String(150), nullable=False)
    name_normalized = Column(String(150), nullable=False)

    commune = relationship("Commune", back_populates="fokontany")

    __table_args__ = (
        UniqueConstraint("version_id", "commune_id", "code", name="uq_fokontany_version_commune_code"),
        UniqueConstraint(
            "version_id", "commune_id", "name_normalized", name="uq_fokontany_version_commune_name"
        ),
        CheckConstraint("name <> ''", name="ck_fokontany_name_not_empty"),
        Index("ix_fokontany_version_commune", "version_id", "commune_id"),
    )
