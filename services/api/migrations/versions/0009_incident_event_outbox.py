"""Add versioned incident event envelopes and transactional outbox."""

from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_incident_event_outbox"
down_revision: str | None = "0008_sla_assignment_and_escalation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.add_column("incident_events", sa.Column("schema_version", sa.Text(), nullable=False, server_default="1"))
    op.add_column("incident_events", sa.Column("aggregate_version", sa.BigInteger(), nullable=False, server_default="1"))
    op.add_column("incident_events", sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("incident_events", sa.Column("causation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_table(
        "event_outbox",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("partition_key", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.Text(), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id", "incident_event_id"], ["incident_events.tenant_id", "incident_events.id"]),
        sa.UniqueConstraint("tenant_id", "incident_event_id", "topic"),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 12", name="outbox_attempt_limit"),
    )
    op.create_index("event_outbox_pending_idx", "event_outbox", ["available_at", "created_at"], postgresql_where=sa.text("published_at IS NULL AND dead_lettered_at IS NULL"))
    op.execute("ALTER TABLE event_outbox ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE event_outbox FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY tenant_isolation ON event_outbox USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})")
    op.execute("""
      CREATE FUNCTION protect_outbox_identity() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF NEW.tenant_id <> OLD.tenant_id OR NEW.id <> OLD.id OR
           NEW.incident_event_id <> OLD.incident_event_id OR NEW.topic <> OLD.topic OR
           NEW.partition_key <> OLD.partition_key OR NEW.schema_version <> OLD.schema_version OR
           NEW.payload <> OLD.payload OR NEW.created_at <> OLD.created_at THEN
          RAISE EXCEPTION 'outbox event identity is immutable' USING ERRCODE = '42501';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("CREATE TRIGGER event_outbox_identity_immutable BEFORE UPDATE ON event_outbox FOR EACH ROW EXECUTE FUNCTION protect_outbox_identity()")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("event_outbox")
    op.execute("DROP FUNCTION IF EXISTS protect_outbox_identity()")
    for column in ("causation_id", "correlation_id", "aggregate_version", "schema_version"):
        op.drop_column("incident_events", column)
