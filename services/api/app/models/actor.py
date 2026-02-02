from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Actor(Base):
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True)
    type_personne = Column(String(20), nullable=False)
    nom = Column(String(150), nullable=False)
    prenoms = Column(String(150))
    telephone = Column(String(30), unique=True)
    email = Column(String(255), unique=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    roles = relationship("ActorRole", back_populates="actor")
    auth = relationship("ActorAuth", back_populates="actor", uselist=False)


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
