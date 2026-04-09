# app/models/billing.py
from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from app.utils.time import utcnow

from .base import Base


plan_students = Table(
    "plan_students",
    Base.metadata,
    Column("plan_id", Integer, ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(50), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class Tenant(Base):
    """
    A billing 'owner' (today: just Imago).
    Later: each teacher with their own domain + Asaas account.
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(50), nullable=False, unique=True)  # e.g. "imago"
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    owner_user_id = Column(
    String(50),
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    unique=True,
)
    owner = relationship(
        "User",
        foreign_keys=[owner_user_id],
        back_populates="tenant",
    )


    billing_accounts = relationship(
        "TenantBillingAccount",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    plans = relationship(
        "Plan",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TenantBillingAccount(Base):
    """
    Stores how to talk to the payment provider for this tenant.
    For v1: one row (Asaas key).
    Later: one per teacher.
    """
    __tablename__ = "tenant_billing_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "is_sandbox", name="uq_tenant_provider_env"),
        Index("ix_tenant_billing_accounts_tenant_active", "tenant_id", "active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    provider = Column(String(20), nullable=False)  # "asaas"
    is_sandbox = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)

    # IMPORTANT: treat as secret (env/secret manager at runtime; DB encryption later if needed)
    api_key = Column(Text, nullable=False)

    # Used to validate Asaas webhook calls (asaas-access-token header)
    webhook_auth_token = Column(String(120), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    tenant = relationship("Tenant", back_populates="billing_accounts")


class Plan(Base):
    """
    A recurring subscription plan.
    For v1: you likely only need a single plan (cheap monthly).
    """
    __tablename__ = "plans"
    __table_args__ = (
        Index("ix_plans_tenant_active", "tenant_id", "active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(120), nullable=False)  # e.g. "Imago Monthly"
    amount_cents = Column(Integer, nullable=False)  # store in cents
    currency = Column(String(3), nullable=False, default="BRL")

    interval = Column(String(10), nullable=False, default="month")  # keep simple for v1
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    tenant = relationship("Tenant", back_populates="plans")

    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    available_to_all_students = Column(Boolean, nullable=False, default=False)

    eligible_students = relationship(
        "User",
        secondary=plan_students,
        back_populates="eligible_plans",
    )


class Subscription(Base):
    """
    Internal subscription record. Webhooks update this.
    Status is your internal truth (not the provider's).
    """
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_tenant_user", "tenant_id", "user_id"),
        Index("ix_subscriptions_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Your users.id is String(50)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)

    # Keep as string to avoid DB enum pain early:
    # "active" | "past_due" | "canceled" | "incomplete"
    status = Column(String(20), nullable=False, default="incomplete")

    provider = Column(String(20), nullable=False, default="asaas")
    provider_subscription_id = Column(String(80), nullable=True)  # fill after creation

    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)

    cancel_at_period_end = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    tenant = relationship("Tenant")
    plan = relationship("Plan", back_populates="subscriptions")

    payments = relationship(
        "Payment",
        back_populates="subscription",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user = relationship("User", back_populates="subscriptions")


class Payment(Base):
    """
    One Asaas PIX charge attempt/record.
    Subscriptions can generate multiple payments over time.
    """
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("provider", "provider_payment_id", name="uq_provider_payment_id"),
        Index("ix_payments_tenant_user", "tenant_id", "user_id"),
        Index("ix_payments_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)

    provider = Column(String(20), nullable=False, default="asaas")
    provider_payment_id = Column(String(80), nullable=False)

    # "pending" | "paid" | "canceled" | "refunded" | "failed"
    status = Column(String(20), nullable=False, default="pending")

    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")

    billing_type = Column(String(10), nullable=False, default="PIX")

    # Optional cache fields (nice for rendering without extra API call)
    pix_qr_code = Column(Text, nullable=True)
    pix_copy_paste = Column(Text, nullable=True)

    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    subscription = relationship("Subscription", back_populates="payments")
    tenant = relationship("Tenant")

    user = relationship("User", back_populates="payments")


class WebhookEvent(Base):
    """
    Inbox for idempotency + debugging.
    Store raw payload. Mark processed once handled successfully.
    """
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "dedupe_key", name="uq_webhook_dedupe"),
        Index("ix_webhook_events_processed", "processed_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(20), nullable=False, default="asaas")

    event_type = Column(String(60), nullable=False)
    dedupe_key = Column(String(120), nullable=False)  # you compute (see webhook handler later)

    payload_json = Column(JSON, nullable=False)

    received_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)

    tenant = relationship("Tenant")