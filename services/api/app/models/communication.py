from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.models.base import Base


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True)
    requester_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    target_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending|accepted|rejected
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    decided_at = Column(DateTime(timezone=True))


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True)
    contact_request_id = Column(Integer, ForeignKey("contact_requests.id"))
    sender_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    receiver_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime(timezone=True))
