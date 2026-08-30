"""Add SLA clocks, ownership history, pause intervals and escalations."""

from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_sla_assignment_and_escalation"
down_revision: str | None = "0007_priority_and_severity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def _secure(table: str, immutable: bool = False) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY tenant_isolation ON {table} USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})")
    if immutable:
        op.execute(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation()")


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.create_table("support_queues", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("name", sa.Text(), nullable=False), sa.Column("category", sa.Text(), nullable=False), sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("required_skill", sa.Text(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.PrimaryKeyConstraint("tenant_id", "id"), sa.ForeignKeyConstraint(["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]), sa.UniqueConstraint("tenant_id", "name"))
    _secure("support_queues")
    op.create_table("incident_assignments", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("queue_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True), sa.PrimaryKeyConstraint("tenant_id", "id"), sa.ForeignKeyConstraint(["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]), sa.ForeignKeyConstraint(["tenant_id", "queue_id"], ["support_queues.tenant_id", "support_queues.id"]), sa.ForeignKeyConstraint(["tenant_id", "assignee_id"], ["users.tenant_id", "users.id"]), sa.CheckConstraint("ended_at IS NULL OR ended_at > assigned_at", name="assignment_window"))
    op.create_index("incident_active_assignment_unique_idx", "incident_assignments", ["tenant_id", "incident_id"], unique=True, postgresql_where=sa.text("ended_at IS NULL"))
    _secure("incident_assignments")
    op.create_table("incident_sla_clocks", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("policy_version", sa.Text(), nullable=False), sa.Column("acknowledgement_due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("unowned_escalation_at", sa.DateTime(timezone=True), nullable=False), sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True), sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True), sa.Column("paused_seconds", sa.BigInteger(), nullable=False, server_default="0"), sa.Column("version", sa.Integer(), nullable=False, server_default="1"), sa.PrimaryKeyConstraint("tenant_id", "incident_id"), sa.ForeignKeyConstraint(["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]))
    _secure("incident_sla_clocks")
    op.create_table("sla_pause_intervals", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("reason", sa.Text(), nullable=False), sa.Column("authorized_by", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expected_resume_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True), sa.PrimaryKeyConstraint("tenant_id", "id"), sa.ForeignKeyConstraint(["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]), sa.CheckConstraint("reason IN ('waiting_for_employee','waiting_for_approved_vendor','approved_change_window')", name="sla_pause_reason"), sa.CheckConstraint("expected_resume_at > started_at", name="sla_expected_resume"))
    op.create_index("sla_one_open_pause_idx", "sla_pause_intervals", ["tenant_id", "incident_id"], unique=True, postgresql_where=sa.text("ended_at IS NULL"))
    _secure("sla_pause_intervals")
    op.create_table("sla_escalation_events", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("policy_version", sa.Text(), nullable=False), sa.Column("level", sa.Text(), nullable=False), sa.Column("deduplication_key", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("tenant_id", "id"), sa.ForeignKeyConstraint(["tenant_id", "incident_id"], ["incidents.tenant_id", "incidents.id"]), sa.UniqueConstraint("tenant_id", "deduplication_key"))
    _secure("sla_escalation_events", immutable=True)


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    for table in ("sla_escalation_events", "sla_pause_intervals", "incident_sla_clocks", "incident_assignments", "support_queues"):
        op.drop_table(table)
