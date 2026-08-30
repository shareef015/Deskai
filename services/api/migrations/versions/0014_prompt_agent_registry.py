"""immutable prompt and agent registry

Revision ID: 0014_prompt_agent_registry
Revises: 0013_graph_replay_provenance
"""
from alembic import op
revision="0014_prompt_agent_registry";down_revision="0013_graph_replay_provenance";branch_labels=None;depends_on=None
def upgrade()->None:
 op.execute("""
 CREATE TABLE ai_configuration_artifacts (tenant_id uuid NOT NULL, artifact_id uuid NOT NULL, artifact_type text NOT NULL CHECK (artifact_type IN ('prompt','agent_configuration','release_bundle')), name text NOT NULL, semantic_version text NOT NULL, lifecycle text NOT NULL CHECK (lifecycle IN ('draft','validated','approved','active','retired','rejected')), content jsonb NOT NULL, content_sha256 char(64) NOT NULL, author_id text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (tenant_id,artifact_id), UNIQUE (tenant_id,artifact_type,name,semantic_version), UNIQUE (tenant_id,content_sha256));
 CREATE TABLE ai_configuration_approvals (tenant_id uuid NOT NULL, approval_id uuid NOT NULL, artifact_id uuid NOT NULL, approver_id text NOT NULL, decision text NOT NULL CHECK (decision IN ('approved','rejected')), evidence jsonb NOT NULL, decided_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (tenant_id,approval_id), FOREIGN KEY (tenant_id,artifact_id) REFERENCES ai_configuration_artifacts(tenant_id,artifact_id));
 CREATE TABLE ai_configuration_deployments (tenant_id uuid NOT NULL, event_id uuid NOT NULL, release_artifact_id uuid NOT NULL, configuration_fingerprint char(64) NOT NULL, mode text NOT NULL CHECK (mode IN ('canary','active','rolled_back')), percentage integer NOT NULL CHECK (percentage BETWEEN 0 AND 100), actor_id text NOT NULL, previous_fingerprint char(64), created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (tenant_id,event_id), FOREIGN KEY (tenant_id,release_artifact_id) REFERENCES ai_configuration_artifacts(tenant_id,artifact_id));
 ALTER TABLE ai_configuration_artifacts ENABLE ROW LEVEL SECURITY; ALTER TABLE ai_configuration_artifacts FORCE ROW LEVEL SECURITY; ALTER TABLE ai_configuration_approvals ENABLE ROW LEVEL SECURITY; ALTER TABLE ai_configuration_approvals FORCE ROW LEVEL SECURITY; ALTER TABLE ai_configuration_deployments ENABLE ROW LEVEL SECURITY; ALTER TABLE ai_configuration_deployments FORCE ROW LEVEL SECURITY;
 CREATE POLICY ai_configuration_artifacts_tenant ON ai_configuration_artifacts USING (tenant_id=current_setting('app.tenant_id',true)::uuid) WITH CHECK (tenant_id=current_setting('app.tenant_id',true)::uuid);
 CREATE POLICY ai_configuration_approvals_tenant ON ai_configuration_approvals USING (tenant_id=current_setting('app.tenant_id',true)::uuid) WITH CHECK (tenant_id=current_setting('app.tenant_id',true)::uuid);
 CREATE POLICY ai_configuration_deployments_tenant ON ai_configuration_deployments USING (tenant_id=current_setting('app.tenant_id',true)::uuid) WITH CHECK (tenant_id=current_setting('app.tenant_id',true)::uuid);
 """)
def downgrade()->None:op.execute("SELECT pg_advisory_xact_lock(4453751966087771)");op.execute("DROP TABLE IF EXISTS ai_configuration_deployments CASCADE");op.execute("DROP TABLE IF EXISTS ai_configuration_approvals CASCADE");op.execute("DROP TABLE IF EXISTS ai_configuration_artifacts CASCADE")
