from __future__ import annotations

import json
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ALLOWED_JOB_TYPES = frozenset({"publish_outbox", "evaluate_sla", "collect_diagnostic", "ingest_knowledge", "run_evaluation"})
NON_RETRYABLE = frozenset({"invalid_payload", "unsupported_job_type", "authorization_denied", "tenant_mismatch"})


@dataclass(frozen=True, slots=True)
class JobEnvelope:
    tenant_id: UUID
    job_type: str
    idempotency_key: str
    payload: Mapping[str, Any]
    priority: int = 50
    schema_version: str = "1"


class DurableJobStore:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def enqueue(self, job: JobEnvelope) -> UUID:
        if job.tenant_id != self._tenant_id or job.job_type not in ALLOWED_JOB_TYPES:
            raise ValueError("job scope or type rejected")
        if not 1 <= job.priority <= 100 or not job.idempotency_key:
            raise ValueError("job priority or idempotency key rejected")
        if len(json.dumps(dict(job.payload), separators=(",", ":")).encode()) > 65_536:
            raise ValueError("job payload too large")
        job_id = uuid4()
        if {str(key).lower() for key in job.payload} & {"password", "authorization", "access_token", "private_key", "hidden_reasoning"}:
            raise ValueError("prohibited job payload field")
        result = await self._session.execute(text("""
          INSERT INTO durable_jobs(tenant_id,id,job_type,schema_version,payload,idempotency_key,status,priority,attempt_count,max_attempts,available_at,created_at)
          VALUES(:tenant_id,:id,:job_type,:schema_version,CAST(:payload AS jsonb),:idempotency_key,'pending',:priority,0,8,:now,:now)
          ON CONFLICT (tenant_id,job_type,idempotency_key)
          DO UPDATE SET idempotency_key=EXCLUDED.idempotency_key RETURNING id
        """), {"tenant_id": self._tenant_id, "id": job_id, "job_type": job.job_type, "schema_version": job.schema_version, "payload": dict(job.payload), "idempotency_key": job.idempotency_key, "priority": job.priority, "now": datetime.now(UTC)})
        return result.scalar_one()

    async def claim(self, worker_id: str) -> Mapping[str, Any] | None:
        lease_token = secrets.token_urlsafe(32)
        result = await self._session.execute(text("""
          WITH candidate AS (
            SELECT id FROM durable_jobs
            WHERE tenant_id=:tenant_id AND status='pending' AND available_at<=:now
            ORDER BY priority, available_at, created_at FOR UPDATE SKIP LOCKED LIMIT 1
          )
          UPDATE durable_jobs j SET status='leased', lease_token=:lease_token,
            lease_owner=:worker_id, lease_expires_at=:lease_expires,
            attempt_count=j.attempt_count+1
          FROM candidate c WHERE j.tenant_id=:tenant_id AND j.id=c.id
          RETURNING j.*
        """), {"tenant_id": self._tenant_id, "now": datetime.now(UTC), "lease_token": lease_token, "worker_id": worker_id, "lease_expires": datetime.now(UTC) + timedelta(seconds=60)})
        row = result.mappings().first()
        if row is not None:
            await self._session.execute(text("""
              INSERT INTO durable_job_attempts(tenant_id,id,job_id,attempt_number,lease_token_fingerprint,worker_id,started_at)
              VALUES(:tenant_id,:id,:job_id,:attempt,:fingerprint,:worker_id,:started_at)
            """), {"tenant_id": self._tenant_id, "id": uuid4(), "job_id": row["id"], "attempt": row["attempt_count"], "fingerprint": hashlib.sha256(lease_token.encode()).hexdigest(), "worker_id": worker_id, "started_at": datetime.now(UTC)})
        return row

    async def complete(self, job_id: UUID, lease_token: str) -> bool:
        result = await self._session.execute(text("""
          UPDATE durable_jobs SET status='succeeded', completed_at=:now
          WHERE tenant_id=:tenant_id AND id=:id AND status='leased'
            AND lease_token=:lease_token AND lease_expires_at>:now
        """), {"tenant_id": self._tenant_id, "id": job_id, "lease_token": lease_token, "now": datetime.now(UTC)})
        changed = bool(getattr(result, "rowcount", 0) == 1)
        if changed:
            await self._finish_attempt(job_id, "succeeded", None)
        return changed

    async def renew(self, job_id: UUID, lease_token: str) -> bool:
        now = datetime.now(UTC)
        result = await self._session.execute(text("""
          UPDATE durable_jobs SET lease_expires_at=:expires
          WHERE tenant_id=:tenant_id AND id=:id AND status='leased'
            AND lease_token=:lease_token AND lease_expires_at>:now
        """), {"tenant_id": self._tenant_id, "id": job_id, "lease_token": lease_token, "now": now, "expires": now + timedelta(seconds=60)})
        return bool(getattr(result, "rowcount", 0) == 1)

    async def fail(self, job_id: UUID, lease_token: str, error_code: str, *, retry_delay_seconds: float) -> bool:
        now = datetime.now(UTC)
        retryable = error_code not in NON_RETRYABLE
        result = await self._session.execute(text("""
          UPDATE durable_jobs SET
            status=CASE WHEN :retryable AND attempt_count<max_attempts THEN 'pending' ELSE 'dead_lettered' END,
            available_at=:available_at, last_error_code=:error_code,
            dead_lettered_at=CASE WHEN :retryable AND attempt_count<max_attempts THEN NULL ELSE :now END,
            lease_token=NULL, lease_owner=NULL, lease_expires_at=NULL
          WHERE tenant_id=:tenant_id AND id=:id AND status='leased'
            AND lease_token=:lease_token AND lease_expires_at>:now
        """), {"tenant_id": self._tenant_id, "id": job_id, "lease_token": lease_token, "now": now, "retryable": retryable, "available_at": now + timedelta(seconds=max(retry_delay_seconds, 0)), "error_code": error_code})
        changed = bool(getattr(result, "rowcount", 0) == 1)
        if changed:
            await self._finish_attempt(job_id, "retry" if retryable else "dead_lettered", error_code)
        return changed

    async def _finish_attempt(self, job_id: UUID, outcome: str, error_code: str | None) -> None:
        await self._session.execute(text("""
          UPDATE durable_job_attempts SET finished_at=:now, outcome=:outcome, error_code=:error_code
          WHERE tenant_id=:tenant_id AND job_id=:job_id AND finished_at IS NULL
        """), {"tenant_id": self._tenant_id, "job_id": job_id, "now": datetime.now(UTC), "outcome": outcome, "error_code": error_code})
