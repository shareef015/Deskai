from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MODULE=ROOT/"services/ai-service/src/deskpilot_ai/persistence.py";MIGRATION=ROOT/"services/api/migrations/versions/0012_graph_thread_registry.py"
def module():
 spec=importlib.util.spec_from_file_location("checkpoint_persistence",MODULE);assert spec and spec.loader;m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/langgraph-checkpoint-policy.json").read_text());source=MODULE.read_text();migration=MIGRATION.read_text();m=module()
 for token in ("AsyncPostgresSaver","EncryptedSerializer","from_pycryptodome_aes","checkpoint_config","expected_checkpoint_id","assert_resume_scope","cleanup_eligible"):
  if token not in source:errors.append(f"checkpoint implementation missing {token}")
 for token in ("graph_thread_registry","graph_checkpoint_heads","FORCE ROW LEVEL SECURITY","current_setting('app.tenant_id'","configuration_fingerprint","legal_hold","delete_after"):
  if token not in migration:errors.append(f"checkpoint migration missing {token}")
 if policy["maximum_checkpoint_bytes"]!=m.MAX_CHECKPOINT_BYTES or policy["maximum_history_items"]!=m.MAX_HISTORY_ITEMS or policy["lease_seconds"]!=m.LEASE_SECONDS:errors.append("checkpoint policy limits differ")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("PostgreSQL checkpointer and durable execution validation passed")
