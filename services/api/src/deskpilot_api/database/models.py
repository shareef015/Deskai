from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantOwned, Timestamped


class Tenant(Base, Timestamped):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class User(Base, TenantOwned, Timestamped):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    external_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class Device(Base, TenantOwned, Timestamped):
    __tablename__ = "devices"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "assigned_user_id"], ["users.tenant_id", "users.id"]
        ),
        ForeignKeyConstraint(["tenant_id", "asset_id"], ["assets.tenant_id", "assets.id"]),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    assigned_user_id: Mapped[UUID | None] = mapped_column(Uuid)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    operating_system: Mapped[str] = mapped_column(String(20), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(40), nullable=False)
    agent_identity: Mapped[str | None] = mapped_column(String(255))
    asset_id: Mapped[UUID | None] = mapped_column(Uuid)
    edition: Mapped[str | None] = mapped_column(String(100))
    build: Mapped[str | None] = mapped_column(String(50))
    architecture: Mapped[str | None] = mapped_column(String(10))
    enrollment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Incident(Base, TenantOwned):
    __tablename__ = "incidents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "requester_id"], ["users.tenant_id", "users.id"]
        ),
        ForeignKeyConstraint(["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]),
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    requester_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    device_id: Mapped[UUID | None] = mapped_column(Uuid)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new")
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="sev3")
    impact_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    urgency_score: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    priority_policy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_rationale: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    priority_calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IncidentEvent(Base, TenantOwned):
    __tablename__ = "incident_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    incident_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid)
    correlation_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    causation_id: Mapped[UUID | None] = mapped_column(Uuid)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventOutbox(Base, TenantOwned):
    __tablename__ = "event_outbox"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "incident_event_id"],
            ["incident_events.tenant_id", "incident_events.id"],
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    incident_event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    partition_key: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
