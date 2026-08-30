"""Add tenant-scoped LangGraph thread registry and checkpoint head."""
from __future__ import annotations
from typing import Sequence
from alembic import op

revision:str="0012_graph_thread_registry";down_revision:str|None="0011_idempotency_records";branch_labels:str|Sequence[str]|None=None;depends_on:str|Sequence[str]|None=None

UPGRADE_SQL="""
CREATE TABLE graph_thread_registry (
  tenant_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  run_id uuid NOT NULL,
  configuration_fingerprint text NOT NULL CHECK (configuration_fingerprint ~ '^[a-f0-9]{64}$'),
  status text NOT NULL CHECK (status IN ('running','interrupted','completed','failed','cancelled')),
  state_version text NOT NULL,
  legal_hold boolean NOT NULL DEFAULT false,
  delete_after timestamptz,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, thread_id),
  UNIQUE (tenant_id, run_id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id),
  FOREIGN KEY (tenant_id, run_id) REFERENCES ai_runs(tenant_id, id)
);
CREATE TABLE graph_checkpoint_heads (
  tenant_id uuid NOT NULL,
  thread_id uuid NOT NULL,
  checkpoint_id text,
  checkpoint_version bigint NOT NULL DEFAULT 0 CHECK (checkpoint_version >= 0),
  state_version text NOT NULL,
  state_sha256 text CHECK (state_sha256 IS NULL OR state_sha256 ~ '^[a-f0-9]{64}$'),
  lease_owner text,
  lease_expires_at timestamptz,
  updated_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, thread_id),
  FOREIGN KEY (tenant_id, thread_id) REFERENCES graph_thread_registry(tenant_id, thread_id) ON DELETE CASCADE
);
CREATE INDEX graph_thread_retention_idx ON graph_thread_registry (tenant_id, delete_after, thread_id) WHERE delete_after IS NOT NULL AND legal_hold = false;
ALTER TABLE graph_thread_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE graph_thread_registry FORCE ROW LEVEL SECURITY;
ALTER TABLE graph_checkpoint_heads ENABLE ROW LEVEL SECURITY;
ALTER TABLE graph_checkpoint_heads FORCE ROW LEVEL SECURITY;
CREATE POLICY graph_thread_tenant_isolation ON graph_thread_registry USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY graph_checkpoint_head_tenant_isolation ON graph_checkpoint_heads USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
"""
def upgrade()->None:op.execute("SELECT pg_advisory_xact_lock(4453751966087771)");op.execute(UPGRADE_SQL)
def downgrade()->None:
 op.execute("SELECT pg_advisory_xact_lock(4453751966087771)");op.execute("DROP TABLE IF EXISTS graph_checkpoint_heads CASCADE");op.execute("DROP TABLE IF EXISTS graph_thread_registry CASCADE")
