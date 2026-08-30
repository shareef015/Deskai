from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("workspace_validator",ROOT/"scripts/validate_incident_workspace_ui.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);SOURCE=(ROOT/"apps/web/src/app/incident-workspace/page.tsx").read_text();CSS=(ROOT/"apps/web/src/app/globals.css").read_text()
class IncidentWorkspaceUITests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_reconnect_uses_cursor(self):self.assertIn("after_cursor=${state.lastCursor}",SOURCE)
 def test_duplicate_events_are_suppressed(self):self.assertIn("event.cursor<=state.lastCursor",SOURCE)
 def test_timeline_is_bounded(self):self.assertIn("slice(-100)",SOURCE)
 def test_environment_boundary_is_explicit(self):self.assertIn("Synthetic recruiter demonstration",SOURCE);self.assertIn("Live authorized tenant",SOURCE)
 def test_interrupt_uses_form_not_browser_dialog(self):self.assertIn("submitDecision",SOURCE);self.assertNotIn("window.prompt",SOURCE);self.assertNotIn("alert(",SOURCE)
 def test_status_updates_are_accessible(self):self.assertIn('role="status"',SOURCE);self.assertIn('aria-live="polite"',SOURCE)
 def test_responsive_and_reduced_motion(self):self.assertIn("@media(max-width:800px)",CSS);self.assertIn("prefers-reduced-motion",CSS)
 def test_runtime_fields_are_allowlisted(self):self.assertIn("ALLOWED_FIELDS",SOURCE);self.assertIn("some(key=>!ALLOWED_FIELDS.has(key))",SOURCE)
if __name__=="__main__":unittest.main()
