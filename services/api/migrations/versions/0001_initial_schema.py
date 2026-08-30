"""Create the initial tenant-safe DeskPilot schema."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Sequence

from alembic import op


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA_SHA256 = "a067b6d721dfee8730e63d9674289ec9822a6107ae54f3ff990b99bf593a9f82"
DROP_ORDER = (
    "audit_events", "ai_checkpoints", "ai_runs", "verification_results",
    "remediation_executions", "remediation_plans", "approval_decisions",
    "consent_decisions", "evidence_items", "incident_events", "incidents",
    "devices", "users", "tenants",
)


def _baseline_sql() -> str:
    path = Path(__file__).resolve().parents[4] / "db" / "schema.sql"
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != SCHEMA_SHA256:
        raise RuntimeError("baseline schema drift detected; create a new revision")
    return payload.decode("utf-8")


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.execute(_baseline_sql())


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    for table in DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP TYPE IF EXISTS decision_value")
    op.execute("DROP TYPE IF EXISTS incident_status")
