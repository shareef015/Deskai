from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.conversation_stream")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/conversation-stream-policy.json").read_text());config=json.loads((ROOT/"config/agents/conversation-stream.json").read_text());m=module();ui=(ROOT/"apps/web/src/app/incident-workspace/conversation-panel.tsx").read_text()
 if policy["requirements"].get("bounded_messages")!=m.MAX_MESSAGES or config.get("maximum_message_characters")!=m.MAX_MESSAGE_CHARS:errors.append("conversation bounds drift")
 if policy["requirements"].get("attachment_uploads_enabled") is not False or config.get("attachments")!=[]:errors.append("attachments must remain disabled")
 for marker in ("idempotency-key","maxLength={MAX_CHARS}",'aria-live="polite"',"Stop support","Do not include passwords"):
  if marker not in ui:errors.append(f"conversation UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("conversation stream validation passed")
