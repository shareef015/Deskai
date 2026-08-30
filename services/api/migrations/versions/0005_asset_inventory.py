"""Add organizational inventory and temporal device assignments."""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0005_asset_inventory"
down_revision: str | None = "0004_role_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TENANT_TABLES = ("departments", "locations", "assets", "device_assignments")
TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        f"USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})"
    )


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    for table in ("departments", "locations"):
        op.create_table(
            table,
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.Text(), nullable=False),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("status", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("tenant_id", "id"),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.UniqueConstraint("tenant_id", "code"),
        )
        _enable_rls(table)
    op.create_table(
        "assets",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_tag", sa.Text(), nullable=False),
        sa.Column("asset_type", sa.Text(), nullable=False),
        sa.Column("serial_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]),
        sa.UniqueConstraint("tenant_id", "asset_tag"),
        sa.CheckConstraint("serial_fingerprint IS NULL OR serial_fingerprint ~ '^[a-f0-9]{64}$'", name="asset_serial_hash"),
    )
    _enable_rls("assets")
    op.add_column("devices", sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("devices", sa.Column("edition", sa.Text(), nullable=True))
    op.add_column("devices", sa.Column("build", sa.Text(), nullable=True))
    op.add_column("devices", sa.Column("architecture", sa.Text(), nullable=True))
    op.add_column("devices", sa.Column("enrollment_status", sa.Text(), nullable=False, server_default="pending"))
    op.add_column("devices", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.create_foreign_key("fk_devices_asset", "devices", "assets", ["tenant_id", "asset_id"], ["tenant_id", "id"])
    op.create_table(
        "device_assignments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_type", sa.Text(), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["users.tenant_id", "users.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "assigned_by"], ["users.tenant_id", "users.id"]),
        sa.CheckConstraint("assignment_type IN ('primary','shared','temporary')", name="assignment_type"),
        sa.CheckConstraint("valid_until IS NULL OR valid_until > valid_from", name="assignment_validity"),
    )
    op.create_index(
        "device_primary_assignment_unique_idx",
        "device_assignments",
        ["tenant_id", "device_id"],
        unique=True,
        postgresql_where=sa.text("assignment_type = 'primary' AND valid_until IS NULL"),
    )
    op.create_index("device_assignments_user_idx", "device_assignments", ["tenant_id", "user_id", "valid_until"])
    _enable_rls("device_assignments")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.drop_table("device_assignments")
    op.drop_constraint("fk_devices_asset", "devices", type_="foreignkey")
    for column in ("version", "last_seen_at", "enrollment_status", "architecture", "build", "edition", "asset_id"):
        op.drop_column("devices", column)
    op.drop_table("assets")
    op.drop_table("locations")
    op.drop_table("departments")
