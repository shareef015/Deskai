from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("browser_validator",ROOT/"scripts/validate_recruiter_browser.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);B=V.module();STEPS=tuple(B.BrowserStep(name,name,"visible","passed") for name in sorted(B.REQUIRED_STEPS));SHOTS=(B.ScreenshotEvidence("desktop","evidence/browser/desktop.png","a"*64,1440,1000,"desktop"),B.ScreenshotEvidence("mobile","evidence/browser/mobile.png","b"*64,390,844,"mobile"))
class DemoBrowserEvidenceTests(unittest.TestCase):
 def test_policy_and_spec_valid(self):self.assertEqual(V.validate(),[])
 def test_complete_run_passes(self):self.assertEqual(B.certify("r","s","c"*64,"seed",STEPS,SHOTS,0).result,"passed")
 def test_missing_step_is_denied(self):
  with self.assertRaises(B.BrowserEvidenceDenied):B.certify("r","s","c"*64,"seed",STEPS[:-1],SHOTS,0)
 def test_duplicate_step_is_denied(self):
  with self.assertRaises(B.BrowserEvidenceDenied):B.certify("r","s","c"*64,"seed",STEPS+(STEPS[0],),SHOTS,0)
 def test_failed_step_fails_run(self):
  steps=STEPS[:-1]+(B.BrowserStep(STEPS[-1].step_id,"x","x","failed"),);self.assertEqual(B.certify("r","s","c"*64,"seed",steps,SHOTS,0).result,"failed")
 def test_console_error_fails_run(self):self.assertEqual(B.certify("r","s","c"*64,"seed",STEPS,SHOTS,1).result,"failed")
 def test_mobile_and_desktop_required(self):
  with self.assertRaises(B.BrowserEvidenceDenied):B.certify("r","s","c"*64,"seed",STEPS,SHOTS[:1],0)
 def test_screenshot_hash_required(self):
  bad=(B.ScreenshotEvidence("d","evidence/browser/d.png","short",1440,1000,"desktop"),SHOTS[1])
  with self.assertRaises(B.BrowserEvidenceDenied):B.certify("r","s","c"*64,"seed",STEPS,bad,0)
 def test_provenance_is_deterministic(self):self.assertEqual(B.certify("r","s","c"*64,"seed",STEPS,SHOTS,0).provenance_sha256,B.certify("r","s","c"*64,"seed",STEPS,SHOTS,0).provenance_sha256)
if __name__=="__main__":unittest.main()
