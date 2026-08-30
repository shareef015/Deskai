import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services/api"


def validate() -> None:
    project = (API / "pyproject.toml").read_text()
    app = (API / "src/deskpilot_api/app.py").read_text()
    health = (API / "src/deskpilot_api/routes/health.py").read_text()
    middleware = (API / "src/deskpilot_api/middleware.py").read_text()
    assert re.search(r'"fastapi>=.*<1"', project)
    assert "def create_app()" in app and "docs_url=None" in app
    assert "/health/live" in health and "/health/ready" in health
    assert "x-correlation-id" in middleware


if __name__ == "__main__":
    validate()
    print("api foundation: valid")
