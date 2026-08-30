"""Enforce immutable audit chains and evidence lineage."""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0006_audit_and_evidence_lineage"
down_revision: str | None = "0005_asset_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_EXPRESSION = "tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.add_column("evidence_items", sa.Column("source_type", sa.Text(), nullable=True))
    op.add_column("evidence_items", sa.Column("source_reference", sa.Text(), nullable=True))
    op.add_column("evidence_items", sa.Column("collector_version", sa.Text(), nullable=True))
    op.add_column("evidence_items", sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("evidence_items", sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "evidence_lineage_edges",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transformation", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.Text(), nullable=False),
        sa.Column("tool_version", sa.Text(), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "parent_evidence_id"],
            ["evidence_items.tenant_id", "evidence_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "child_evidence_id"],
            ["evidence_items.tenant_id", "evidence_items.id"],
        ),
        sa.CheckConstraint("parent_evidence_id <> child_evidence_id", name="lineage_no_self_edge"),
        sa.UniqueConstraint("tenant_id", "parent_evidence_id", "child_evidence_id", "transformation"),
    )
    op.create_index(
        "evidence_lineage_child_idx",
        "evidence_lineage_edges",
        ["tenant_id", "child_evidence_id", "created_at"],
    )
    op.execute("ALTER TABLE evidence_lineage_edges ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE evidence_lineage_edges FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON evidence_lineage_edges "
        f"USING ({TENANT_EXPRESSION}) WITH CHECK ({TENANT_EXPRESSION})"
    )
    op.execute(
        """
        CREATE FUNCTION reject_immutable_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'immutable history cannot be modified' USING ERRCODE = '42501';
        END;
        $$
        """
    )
    for table in ("audit_events", "incident_events", "evidence_lineage_edges"):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation()"
        )
    op.execute(
        """
        CREATE FUNCTION append_audit_event(
          p_tenant_id uuid, p_event_type text, p_actor_type text, p_actor_id uuid,
          p_resource_type text, p_resource_id uuid, p_correlation_id uuid, p_payload jsonb
        ) RETURNS TABLE(event_id uuid, sequence_number bigint, event_hash text)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        DECLARE
          v_id uuid := gen_random_uuid();
          v_sequence bigint;
          v_previous text;
          v_hash text;
          v_occurred timestamptz := clock_timestamp();
        BEGIN
          PERFORM pg_advisory_xact_lock(hashtextextended(p_tenant_id::text, 0));
          SELECT a.sequence_number, a.event_hash INTO v_sequence, v_previous
            FROM audit_events a WHERE a.tenant_id = p_tenant_id
            ORDER BY a.sequence_number DESC LIMIT 1;
          v_sequence := coalesce(v_sequence, 0) + 1;
          v_hash := encode(digest(concat_ws('|', p_tenant_id::text, v_sequence::text,
            coalesce(v_previous, ''), p_event_type, p_actor_type, coalesce(p_actor_id::text, ''),
            p_resource_type, p_resource_id::text, p_correlation_id::text,
            p_payload::text, v_occurred::text), 'sha256'), 'hex');
          INSERT INTO audit_events(id, tenant_id, sequence_number, event_type, actor_type,
            actor_id, resource_type, resource_id, correlation_id, previous_hash, event_hash,
            payload, occurred_at)
          VALUES(v_id, p_tenant_id, v_sequence, p_event_type, p_actor_type, p_actor_id,
            p_resource_type, p_resource_id, p_correlation_id, v_previous, v_hash,
            p_payload, v_occurred);
          RETURN QUERY SELECT v_id, v_sequence, v_hash;
        END;
        $$
        """
    )
    op.execute("REVOKE INSERT, UPDATE, DELETE ON audit_events FROM deskpilot_runtime")
    op.execute("REVOKE ALL ON FUNCTION append_audit_event(uuid,text,text,uuid,text,uuid,uuid,jsonb) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION append_audit_event(uuid,text,text,uuid,text,uuid,uuid,jsonb) TO deskpilot_runtime")


def downgrade() -> None:
    op.execute("SELECT pg_advisory_xact_lock(4453751966087771)")
    op.execute("DROP FUNCTION IF EXISTS append_audit_event(uuid,text,text,uuid,text,uuid,uuid,jsonb)")
    for table in ("evidence_lineage_edges", "incident_events", "audit_events"):
        op.execute(f"DROP TRIGGER IF EXISTS {table}_immutable ON {table}")
    op.execute("DROP FUNCTION IF EXISTS reject_immutable_mutation()")
    op.drop_table("evidence_lineage_edges")
    for column in ("legal_hold", "retention_until", "collector_version", "source_reference", "source_type"):
        op.drop_column("evidence_items", column)
