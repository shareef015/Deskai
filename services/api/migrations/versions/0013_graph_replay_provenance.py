"""Add tenant-scoped graph replay and state-migration provenance."""
from __future__ import annotations
from typing import Sequence
from alembic import op
revision:str="0013_graph_replay_provenance";down_revision:str|None="0012_graph_thread_registry";branch_labels:str|Sequence[str]|None=None;depends_on:str|Sequence[str]|None=None
UPGRADE_SQL="""
CREATE TABLE graph_replay_events (
 tenant_id uuid NOT NULL, event_id uuid NOT NULL, incident_id uuid NOT NULL,
 mode text NOT NULL CHECK (mode IN ('resume','replay','fork')),
 source_thread_id uuid NOT NULL, source_checkpoint_id text NOT NULL,
 source_checkpoint_sha256 text NOT NULL CHECK (source_checkpoint_sha256 ~ '^[a-f0-9]{64}$'),
 target_thread_id uuid NOT NULL, actor_id text NOT NULL,
 configuration_fingerprint text NOT NULL CHECK (configuration_fingerprint ~ '^[a-f0-9]{64}$'),
 fresh_human_decision_required boolean NOT NULL, side_effect_policy text NOT NULL,
 provenance_sha256 text NOT NULL CHECK (provenance_sha256 ~ '^[a-f0-9]{64}$'), created_at timestamptz NOT NULL,
 PRIMARY KEY (tenant_id,event_id), FOREIGN KEY (tenant_id,incident_id) REFERENCES incidents(tenant_id,id)
);
CREATE TABLE graph_state_migration_events (
 tenant_id uuid NOT NULL, event_id uuid NOT NULL, replay_event_id uuid NOT NULL,
 source_version text NOT NULL, target_version text NOT NULL, migration_index integer NOT NULL CHECK (migration_index >= 0),
 state_before_sha256 text NOT NULL CHECK (state_before_sha256 ~ '^[a-f0-9]{64}$'),
 state_after_sha256 text NOT NULL CHECK (state_after_sha256 ~ '^[a-f0-9]{64}$'), created_at timestamptz NOT NULL,
 PRIMARY KEY (tenant_id,event_id), FOREIGN KEY (tenant_id,replay_event_id) REFERENCES graph_replay_events(tenant_id,event_id)
);
ALTER TABLE graph_replay_events ENABLE ROW LEVEL SECURITY;ALTER TABLE graph_replay_events FORCE ROW LEVEL SECURITY;
ALTER TABLE graph_state_migration_events ENABLE ROW LEVEL SECURITY;ALTER TABLE graph_state_migration_events FORCE ROW LEVEL SECURITY;
CREATE POLICY graph_replay_tenant_isolation ON graph_replay_events USING (tenant_id=current_setting('app.tenant_id',true)::uuid) WITH CHECK (tenant_id=current_setting('app.tenant_id',true)::uuid);
CREATE POLICY graph_migration_tenant_isolation ON graph_state_migration_events USING (tenant_id=current_setting('app.tenant_id',true)::uuid) WITH CHECK (tenant_id=current_setting('app.tenant_id',true)::uuid);
"""
def upgrade()->None:op.execute("SELECT pg_advisory_xact_lock(4453751966087771)");op.execute(UPGRADE_SQL)
def downgrade()->None:op.execute("SELECT pg_advisory_xact_lock(4453751966087771)");op.execute("DROP TABLE IF EXISTS graph_state_migration_events CASCADE");op.execute("DROP TABLE IF EXISTS graph_replay_events CASCADE")
