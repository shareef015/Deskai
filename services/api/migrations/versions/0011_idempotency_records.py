"""Add tenant-scoped encrypted idempotency replay records."""

from __future__ import annotations
from typing import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_idempotency_records"
down_revision: str | None = "0010_durable_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.create_table(
        "idempotency_records",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("idempotency_key_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("owner_token_hash", sa.String(length=64), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_status", sa.SmallInteger(), nullable=True),
        sa.Column("response_headers", postgresql.JSONB(), nullable=True),
        sa.Column("response_envelope", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "operation", "idempotency_key_hash"),
        sa.CheckConstraint("status IN ('in_progress','completed')", name="idempotency_status"),
    )
    op.create_index("idempotency_expiry_idx", "idempotency_records", ["expires_at"])
    op.execute("ALTER TABLE idempotency_records ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idempotency_records FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY tenant_isolation ON idempotency_records USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})")
    op.execute("""
      CREATE FUNCTION protect_idempotency_identity() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF NEW.tenant_id<>OLD.tenant_id OR NEW.operation<>OLD.operation OR
           NEW.idempotency_key_hash<>OLD.idempotency_key_hash OR
           NEW.request_fingerprint<>OLD.request_fingerprint OR NEW.created_at<>OLD.created_at THEN
          RAISE EXCEPTION 'idempotency identity is immutable' USING ERRCODE='42501';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("CREATE TRIGGER idempotency_identity_immutable BEFORE UPDATE ON idempotency_records FOR EACH ROW EXECUTE FUNCTION protect_idempotency_identity()")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("idempotency_records")
    op.execute("DROP FUNCTION IF EXISTS protect_idempotency_identity()")
