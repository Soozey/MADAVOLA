from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class PaymentProvider(Base):
    __tablename__ = "payment_providers"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)
    config_json = Column(Text)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("payment_providers.id"), nullable=False)
    payer_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    payee_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False)
    fee_id = Column(Integer, ForeignKey("fees.id"))
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    external_ref = Column(String(80), nullable=False, unique=True)
    idempotency_key = Column(String(80))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    provider = relationship("PaymentProvider")
    fee = relationship("Fee", back_populates="payment_requests")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    payment_request_id = Column(Integer, ForeignKey("payment_requests.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    operator_ref = Column(String(120))
    confirmed_at = Column(DateTime(timezone=True))

    payment_request = relationship("PaymentRequest")


class WebhookInbox(Base):
    __tablename__ = "webhook_inbox"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("payment_providers.id"), nullable=False)
    external_ref = Column(String(80), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    payload_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="received")

    provider = relationship("PaymentProvider")
