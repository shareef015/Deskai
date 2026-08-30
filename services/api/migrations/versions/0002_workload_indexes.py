"""Add tenant-leading indexes for production query paths."""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_workload_indexes"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    "incidents_open_work_idx",
    "incidents_requester_opened_idx",
    "devices_assigned_user_idx",
    "consent_active_incident_idx",
    "approval_action_lookup_idx",
    "remediation_execution_status_idx",
    "ai_checkpoint_resume_idx",
    "audit_correlation_idx",
)


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.create_index(
        "incidents_open_work_idx",
        "incidents",
        ["tenant_id", "status", "priority", sa.text("opened_at DESC"), "id"],
        postgresql_where=sa.text("closed_at IS NULL"),
    )
    op.create_index(
        "incidents_requester_opened_idx",
        "incidents",
        ["tenant_id", "requester_id", sa.text("opened_at DESC"), "id"],
    )
    op.create_index("devices_assigned_user_idx", "devices", ["tenant_id", "assigned_user_id"])
    op.create_index(
        "consent_active_incident_idx",
        "consent_decisions",
        ["tenant_id", "incident_id", sa.text("expires_at DESC")],
        postgresql_where=sa.text("decision = 'approved'"),
    )
    op.create_index(
        "approval_action_lookup_idx",
        "approval_decisions",
        ["tenant_id", "incident_id", "action_fingerprint", sa.text("expires_at DESC")],
        postgresql_where=sa.text("decision = 'approved'"),
    )
    op.create_index(
        "remediation_execution_status_idx",
        "remediation_executions",
        ["tenant_id", "incident_id", "status", sa.text("started_at DESC")],
    )
    op.create_index(
        "ai_checkpoint_resume_idx",
        "ai_checkpoints",
        ["tenant_id", "run_id", sa.text("checkpoint_sequence DESC")],
        unique=True,
    )
    op.create_index("audit_correlation_idx", "audit_events", ["tenant_id", "correlation_id"])


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    for index in reversed(INDEXES):
        op.drop_index(index)
