import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps/web"


def validate() -> None:
    package = json.loads((WEB / "package.json").read_text())
    page = (WEB / "src/app/page.tsx").read_text()
    config = (WEB / "next.config.ts").read_text()
    assert package["private"] is True and package["scripts"]["typecheck"] == "tsc --noEmit"
    assert "How can I help you today?" in page and "without your permission" in page
    assert 'htmlFor="issue"' in page and 'aria-describedby="privacy-note"' in page
    assert 'output: "standalone"' in config and "poweredByHeader: false" in config


if __name__ == "__main__":
    validate()
    print("web foundation: valid")
