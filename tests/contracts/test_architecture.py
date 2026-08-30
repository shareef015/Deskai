from __future__ import annotations
import importlib.util, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("architecture", ROOT / "scripts" / "validate_architecture.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
class ArchitectureTests(unittest.TestCase):
    def test_contract_is_valid(self): self.assertEqual(MODULE.validate(), [])
    def test_ai_is_proposal_only(self): self.assertEqual(MODULE.load()["components"]["ai_service"]["authority"], "proposal_only")
    def test_direct_ai_endpoint_path_is_prohibited(self): self.assertIn("ai_service_direct_to_endpoint_agent", MODULE.load()["prohibited_connections"])
    def test_redis_is_not_durable_truth(self): self.assertEqual(MODULE.load()["data_authority"]["durable_truth"], "postgresql")
