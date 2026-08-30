from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/"services/ai-service/src"
def modules():
 if str(PACKAGE) not in sys.path:sys.path.insert(0,str(PACKAGE))
 return importlib.import_module("deskpilot_ai.migrations"),importlib.import_module("deskpilot_ai.replay")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/graph-resume-replay-migration-policy.json").read_text());migrations,replay=modules();migration_source=(PACKAGE/"deskpilot_ai/migrations.py").read_text();replay_source=(PACKAGE/"deskpilot_ai/replay.py").read_text();sql=(ROOT/"services/api/migrations/versions/0013_graph_replay_provenance.py").read_text()
 for token in ("MigrationRegistry","MigrationStep","upgrade","downgrade","IMMUTABLE_FIELDS","no contiguous migration path"):
  if token not in migration_source:errors.append(f"migration registry missing {token}")
 for token in ("plan_execution","source_checkpoint_sha256","configuration_fingerprint","fresh_human_decision_required","recorded_results_only","new_authorization_required","aupdate_state","ainvoke(None"):
  if token not in replay_source:errors.append(f"replay control missing {token}")
 for token in ("graph_replay_events","graph_state_migration_events","FORCE ROW LEVEL SECURITY","provenance_sha256"):
  if token not in sql:errors.append(f"replay provenance migration missing {token}")
 if policy["current_state_version"]!=migrations.CURRENT_STATE_VERSION or policy["maximum_migration_steps"]!=migrations.MAX_MIGRATION_STEPS:errors.append("migration policy differs")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("graph resume, replay and state migration validation passed")
