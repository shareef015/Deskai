"""Add tenant-scoped, time-bounded enterprise role assignments."""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0004_role_assignments"
down_revision: str | None = "0003_tenant_row_level_security"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.create_table(
        "role_assignments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("scope_type", sa.Text(), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "granted_by"], ["users.tenant_id", "users.id"]),
        sa.CheckConstraint("scope_type IN ('tenant','department','location','device','incident')", name="role_scope"),
        sa.CheckConstraint("valid_until IS NULL OR valid_until > valid_from", name="role_validity"),
        sa.UniqueConstraint("tenant_id", "user_id", "role", "scope_type", "scope_id", "valid_from"),
    )
    op.create_index(
        "role_assignments_active_user_idx",
        "role_assignments",
        ["tenant_id", "user_id", "role", "scope_type", "scope_id"],
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.execute("ALTER TABLE role_assignments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE role_assignments FORCE ROW LEVEL SECURITY")
    expression = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"
    op.execute(
        "CREATE POLICY tenant_isolation ON role_assignments "
        f"USING ({expression}) WITH CHECK ({expression})"
    )


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("role_assignments")
