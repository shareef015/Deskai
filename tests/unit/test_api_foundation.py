import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services/api"


class ApiFoundationTests(unittest.TestCase):
    def test_fastapi_is_bounded(self):
        text = (API / "pyproject.toml").read_text()
        self.assertRegex(text, r'"fastapi>=.*<1"')

    def test_application_uses_factory(self):
        text = (API / "src/deskpilot_api/app.py").read_text()
        self.assertIn("def create_app()", text)

    def test_health_has_live_and_ready_routes(self):
        text = (API / "src/deskpilot_api/routes/health.py").read_text()
        self.assertEqual(len(re.findall(r'@router\.get\("/health/', text)), 2)

    def test_every_response_gets_correlation_id(self):
        text = (API / "src/deskpilot_api/middleware.py").read_text()
        self.assertIn('response.headers["x-correlation-id"]', text)


if __name__ == "__main__":
    unittest.main()
