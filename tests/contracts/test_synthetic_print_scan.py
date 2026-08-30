from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("psval",ROOT/"scripts/validate_synthetic_print_scan.py");assert SPEC and SPEC.loader;V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);P=json.loads((ROOT/"contracts/synthetic-print-scan-policy.json").read_text())
class SyntheticPrintScanTests(unittest.TestCase):
 def test_contract_is_valid(self):self.assertEqual(V.validate(),[])
 def test_device_counts(self):self.assertEqual(P["counts"],{"printers":6,"scanners":3,"print_servers":2})
 def test_signed_drivers_only(self):self.assertTrue(P["requirements"]["signed_drivers_only"])
 def test_test_scan_is_privacy_safe(self):self.assertTrue(P["requirements"]["test_scan_uses_synthetic_sheet"] and P["requirements"]["document_and_image_content_forbidden"])
 def test_faults_are_reversible(self):self.assertTrue(P["requirements"]["faults_explicit_and_reversible"])
