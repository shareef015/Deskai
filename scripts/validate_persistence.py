from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/persistence-policy.json").read_text())
    repository = (ROOT / "services/api/src/deskpilot_api/database/repositories.py").read_text()
    unit = (ROOT / "services/api/src/deskpilot_api/database/unit_of_work.py").read_text()
    session = (ROOT / "services/api/src/deskpilot_api/database/session.py").read_text()
    models = (ROOT / "services/api/src/deskpilot_api/database/models.py").read_text()
    if policy.get("orm") != "sqlalchemy-2-async" or policy.get("driver") != "psycopg-3":
        errors.append("persistence stack changed")
    for token in ("Incident.tenant_id == self._tenant_id", "tenant mismatch", "await self._session.flush()"):
        if token not in repository:
            errors.append(f"tenant repository invariant missing: {token}")
    if ".commit()" in repository:
        errors.append("repository must not own transaction commit")
    for token in ("await self.session.commit()", "await self.session.rollback()", "await self.session.close()"):
        if token not in unit:
            errors.append(f"unit-of-work behavior missing: {token}")
    for token in ("statement_timeout=30000", "lock_timeout=5000", "pool_pre_ping=True"):
        if token not in session:
            errors.append(f"database safety setting missing: {token}")
    if models.count("ForeignKeyConstraint(") < 3:
        errors.append("composite tenant ORM constraints are incomplete")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("SQLAlchemy persistence validation passed")
