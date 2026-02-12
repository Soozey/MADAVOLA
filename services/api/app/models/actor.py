from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.geo import GeoPoint


class Actor(Base):
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True)
    type_personne = Column(String(20), nullable=False)
    nom = Column(String(150), nullable=False)
    prenoms = Column(String(150))
    cin = Column(String(50))
    nif = Column(String(50))
    stat = Column(String(50))
    rccm = Column(String(50))
    telephone = Column(String(30), unique=True)
    email = Column(String(255), unique=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    commune_id = Column(Integer, ForeignKey("communes.id"), nullable=False)
    fokontany_id = Column(Integer, ForeignKey("fokontany.id"))
    territory_version_id = Column(Integer, ForeignKey("territory_versions.id"), nullable=False)
    signup_geo_point_id = Column(Integer, ForeignKey("geo_points.id"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    roles = relationship("ActorRole", back_populates="actor")
    auth = relationship("ActorAuth", back_populates="actor", uselist=False)
    # geo_points relationship removed temporarily due to ambiguous foreign key issue
    # Can be re-added later with proper foreign_keys specification if needed


class ActorRole(Base):
    __tablename__ = "actor_roles"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    role = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))

    actor = relationship("Actor", back_populates="roles")


class ActorAuth(Base):
    __tablename__ = "actor_auth"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)

    actor = relationship("Actor", back_populates="auth")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    token_id = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
