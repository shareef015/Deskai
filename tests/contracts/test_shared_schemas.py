import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SharedSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = json.loads((ROOT / "contracts/openapi/deskpilot-v1.json").read_text())

    def test_openapi_is_current(self):
        self.assertEqual(self.api["openapi"], "3.1.0")

    def test_operations_have_stable_ids(self):
        ids = [op["operationId"] for path in self.api["paths"].values() for op in path.values()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_objects_reject_unknown_fields(self):
        schemas = self.api["components"]["schemas"].values()
        self.assertTrue(all(s.get("additionalProperties") is False for s in schemas))

    def test_python_and_typescript_clients_exist(self):
        self.assertTrue((ROOT / "packages/python/deskpilot-schemas/src/deskpilot_schemas/models.py").is_file())
        self.assertTrue((ROOT / "packages/typescript/api-client/src/client.ts").is_file())


if __name__ == "__main__":
    unittest.main()
