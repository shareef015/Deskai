import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RepositoryStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "contracts/repository-boundaries.json").read_text())

    def test_all_deployable_directories_exist(self):
        self.assertTrue(all((ROOT / p).is_dir() for p in self.contract["deployables"].values()))

    def test_shared_package_roots_exist(self):
        self.assertTrue(all((ROOT / p).is_dir() for p in self.contract["shared_packages"]))

    def test_endpoint_execution_has_one_boundary(self):
        self.assertIn("endpoint_execution_is_available_only_through_mcp_gateway", self.contract["rules"])

    def test_every_deployable_has_ownership_readme(self):
        self.assertTrue(all((ROOT / p / "README.md").is_file() for p in self.contract["deployables"].values()))


if __name__ == "__main__":
    unittest.main()
