-- DeskPilot PostgreSQL logical schema. Migration ownership begins separately.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE incident_status AS ENUM (
  'new', 'triaging', 'investigating', 'awaiting_consent', 'awaiting_approval',
  'remediating', 'verifying', 'resolved', 'escalated', 'cancelled'
);
CREATE TYPE decision_value AS ENUM ('approved', 'rejected', 'expired', 'revoked');

CREATE TABLE tenants (
  id uuid PRIMARY KEY,
  slug text NOT NULL UNIQUE,
  display_name text NOT NULL,
  status text NOT NULL CHECK (status IN ('active', 'suspended', 'closed')),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  CHECK (slug = lower(slug))
);

CREATE TABLE users (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  external_subject text NOT NULL,
  display_name text NOT NULL,
  status text NOT NULL CHECK (status IN ('active', 'disabled')),
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, external_subject)
);

CREATE TABLE devices (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  assigned_user_id uuid,
  hostname text NOT NULL,
  operating_system text NOT NULL CHECK (operating_system IN ('windows_10', 'windows_11')),
  lifecycle_status text NOT NULL,
  agent_identity text,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, hostname),
  FOREIGN KEY (tenant_id, assigned_user_id) REFERENCES users(tenant_id, id)
);

CREATE TABLE incidents (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  requester_id uuid NOT NULL,
  device_id uuid,
  category text NOT NULL CHECK (category IN ('outlook', 'printer', 'scanner', 'windows_network')),
  status incident_status NOT NULL DEFAULT 'new',
  priority smallint NOT NULL CHECK (priority BETWEEN 1 AND 5),
  summary text NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  opened_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  closed_at timestamptz,
  PRIMARY KEY (tenant_id, id),
  FOREIGN KEY (tenant_id, requester_id) REFERENCES users(tenant_id, id),
  FOREIGN KEY (tenant_id, device_id) REFERENCES devices(tenant_id, id),
  CHECK (closed_at IS NULL OR status IN ('resolved', 'cancelled'))
);

CREATE TABLE incident_events (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  sequence_number bigint NOT NULL CHECK (sequence_number > 0),
  event_type text NOT NULL,
  actor_type text NOT NULL CHECK (actor_type IN ('employee', 'engineer', 'administrator', 'service', 'ai')),
  actor_id uuid,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, incident_id, sequence_number),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id)
);

CREATE TABLE evidence_items (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  evidence_type text NOT NULL,
  object_reference text,
  content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[a-f0-9]{64}$'),
  collected_by text NOT NULL,
  classification text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  collected_at timestamptz NOT NULL,
  expires_at timestamptz,
  PRIMARY KEY (tenant_id, id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id)
);

CREATE TABLE consent_decisions (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  employee_id uuid NOT NULL,
  scope jsonb NOT NULL,
  decision decision_value NOT NULL,
  decided_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id),
  FOREIGN KEY (tenant_id, employee_id) REFERENCES users(tenant_id, id),
  CHECK (expires_at > decided_at)
);

CREATE TABLE approval_decisions (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  approver_id uuid NOT NULL,
  action_fingerprint text NOT NULL,
  decision decision_value NOT NULL,
  rationale text,
  decided_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, incident_id, action_fingerprint, approver_id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id),
  FOREIGN KEY (tenant_id, approver_id) REFERENCES users(tenant_id, id),
  CHECK (expires_at > decided_at)
);

CREATE TABLE remediation_plans (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  created_by_type text NOT NULL CHECK (created_by_type IN ('engineer', 'ai')),
  risk_level text NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'prohibited')),
  plan jsonb NOT NULL,
  plan_fingerprint text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, incident_id, plan_fingerprint),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id)
);

CREATE TABLE remediation_executions (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  plan_id uuid NOT NULL,
  approval_id uuid,
  idempotency_key text NOT NULL,
  pre_state_reference text NOT NULL,
  post_state_reference text,
  status text NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'rolled_back')),
  started_at timestamptz,
  completed_at timestamptz,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, idempotency_key),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id),
  FOREIGN KEY (tenant_id, plan_id) REFERENCES remediation_plans(tenant_id, id),
  FOREIGN KEY (tenant_id, approval_id) REFERENCES approval_decisions(tenant_id, id)
);

CREATE TABLE verification_results (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  execution_id uuid,
  technical_passed boolean NOT NULL,
  employee_confirmed boolean,
  evidence_reference text NOT NULL,
  verified_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id),
  FOREIGN KEY (tenant_id, execution_id) REFERENCES remediation_executions(tenant_id, id)
);

CREATE TABLE ai_runs (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  incident_id uuid NOT NULL,
  graph_name text NOT NULL,
  configuration_fingerprint text NOT NULL,
  status text NOT NULL CHECK (status IN ('running', 'interrupted', 'completed', 'failed', 'cancelled')),
  started_at timestamptz NOT NULL,
  completed_at timestamptz,
  PRIMARY KEY (tenant_id, id),
  FOREIGN KEY (tenant_id, incident_id) REFERENCES incidents(tenant_id, id)
);

CREATE TABLE ai_checkpoints (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  run_id uuid NOT NULL,
  checkpoint_sequence bigint NOT NULL CHECK (checkpoint_sequence > 0),
  state_reference text NOT NULL,
  state_sha256 text NOT NULL CHECK (state_sha256 ~ '^[a-f0-9]{64}$'),
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, run_id, checkpoint_sequence),
  FOREIGN KEY (tenant_id, run_id) REFERENCES ai_runs(tenant_id, id)
);

CREATE TABLE audit_events (
  id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  sequence_number bigint NOT NULL CHECK (sequence_number > 0),
  event_type text NOT NULL,
  actor_type text NOT NULL,
  actor_id uuid,
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  correlation_id uuid NOT NULL,
  previous_hash text,
  event_hash text NOT NULL CHECK (event_hash ~ '^[a-f0-9]{64}$'),
  payload jsonb NOT NULL,
  occurred_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, id),
  UNIQUE (tenant_id, sequence_number)
);

CREATE INDEX incidents_tenant_status_opened_idx ON incidents (tenant_id, status, opened_at DESC);
CREATE INDEX incident_events_tenant_incident_time_idx ON incident_events (tenant_id, incident_id, occurred_at);
CREATE INDEX evidence_tenant_incident_time_idx ON evidence_items (tenant_id, incident_id, collected_at DESC);
CREATE INDEX audit_tenant_resource_time_idx ON audit_events (tenant_id, resource_type, resource_id, occurred_at);
