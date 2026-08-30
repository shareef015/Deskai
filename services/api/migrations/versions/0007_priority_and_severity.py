"""Persist deterministic priority classification and governed overrides."""

from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_priority_and_severity"
down_revision: str | None = "0006_audit_and_evidence_lineage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.add_column("incidents", sa.Column("severity", sa.Text(), nullable=False, server_default="sev3"))
    op.add_column("incidents", sa.Column("impact_score", sa.SmallInteger(), nullable=False, server_default="3"))
    op.add_column("incidents", sa.Column("urgency_score", sa.SmallInteger(), nullable=False, server_default="3"))
    op.add_column("incidents", sa.Column("priority_policy_version", sa.Text(), nullable=False, server_default="priority-v1"))
    op.add_column("incidents", sa.Column("priority_rationale", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("incidents", sa.Column("priority_calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_check_constraint("incident_severity", "incidents", "severity IN ('sev1','sev2','sev3','sev4','sev5')")
    op.create_check_constraint("incident_impact_score", "incidents", "impact_score BETWEEN 1 AND 5")
    op.create_check_constraint("incident_urgency_score", "incidents", "urgency_score BETWEEN 1 AND 5")
    op.create_table(
        "incident_priority_overrides",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_priority", sa.SmallInteger(), nullable=False),
        sa.Column("override_priority", sa.SmallInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("authorized_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "authorized_by"], ["users.tenant_id", "users.id"]),
        sa.CheckConstraint("original_priority BETWEEN 1 AND 5 AND override_priority BETWEEN 1 AND 5", name="override_priority_range"),
        sa.CheckConstraint("expires_at > authorized_at", name="override_expiry"),
    )
    op.execute("ALTER TABLE incident_priority_overrides ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE incident_priority_overrides FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation ON incident_priority_overrides " f"USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})")
    op.execute("CREATE TRIGGER incident_priority_overrides_immutable BEFORE UPDATE OR DELETE ON incident_priority_overrides FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation()")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("incident_priority_overrides")
    for column in ("priority_calculated_at", "priority_rationale", "priority_policy_version", "urgency_score", "impact_score", "severity"):
        op.drop_column("incidents", column)
