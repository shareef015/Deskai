import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps/web"


class WebFoundationTests(unittest.TestCase):
    def test_package_is_private(self):
        self.assertTrue(json.loads((WEB / "package.json").read_text())["private"])

    def test_typescript_is_strict(self):
        self.assertTrue(json.loads((WEB / "tsconfig.json").read_text())["compilerOptions"]["strict"])

    def test_greeting_and_permission_language_exist(self):
        page = (WEB / "src/app/page.tsx").read_text()
        self.assertIn("How can I help you today?", page)
        self.assertIn("without your permission", page)

    def test_health_route_exists(self):
        self.assertTrue((WEB / "src/app/api/health/route.ts").is_file())


if __name__ == "__main__":
    unittest.main()
