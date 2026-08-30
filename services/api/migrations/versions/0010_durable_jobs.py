"""Add tenant-scoped durable jobs and immutable attempt history."""

from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_durable_jobs"
down_revision: str | None = "0009_incident_event_outbox"
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
    op.create_table(
        "durable_jobs",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority", sa.SmallInteger(), nullable=False),
        sa.Column("attempt_count", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.SmallInteger(), nullable=False, server_default="8"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_token", sa.Text(), nullable=True),
        sa.Column("lease_owner", sa.Text(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "job_type", "idempotency_key"),
        sa.CheckConstraint("status IN ('pending','leased','succeeded','dead_lettered','cancelled')", name="job_status"),
        sa.CheckConstraint("priority BETWEEN 1 AND 100", name="job_priority"),
        sa.CheckConstraint("max_attempts BETWEEN 1 AND 8", name="job_max_attempts"),
    )
    op.create_index("durable_jobs_claim_idx", "durable_jobs", ["tenant_id", "priority", "available_at", "created_at"], postgresql_where=sa.text("status = 'pending'"))
    _secure("durable_jobs")
    op.create_table(
        "durable_job_attempts",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.SmallInteger(), nullable=False),
        sa.Column("lease_token_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id", "job_id"], ["durable_jobs.tenant_id", "durable_jobs.id"]),
        sa.UniqueConstraint("tenant_id", "job_id", "attempt_number"),
    )
    _secure("durable_job_attempts")
    op.execute("""
      CREATE FUNCTION protect_job_attempt_identity() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF NEW.tenant_id <> OLD.tenant_id OR NEW.id <> OLD.id OR NEW.job_id <> OLD.job_id OR
           NEW.attempt_number <> OLD.attempt_number OR
           NEW.lease_token_fingerprint <> OLD.lease_token_fingerprint OR
           NEW.worker_id <> OLD.worker_id OR NEW.started_at <> OLD.started_at THEN
          RAISE EXCEPTION 'job attempt identity is immutable' USING ERRCODE = '42501';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("CREATE TRIGGER durable_job_attempt_identity_immutable BEFORE UPDATE ON durable_job_attempts FOR EACH ROW EXECUTE FUNCTION protect_job_attempt_identity()")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("durable_job_attempts")
    op.execute("DROP FUNCTION IF EXISTS protect_job_attempt_identity()")
    op.drop_table("durable_jobs")
