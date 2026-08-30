import sys
from datetime import UTC
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/python/deskpilot-core/src"))

from deskpilot_core import Result, SystemClock, new_correlation_id  # noqa: E402


def validate() -> None:
    assert len(new_correlation_id()) == 36
    assert SystemClock().now().tzinfo == UTC
    assert Result(value="ok").is_ok
    assert not Result(error="failed").is_ok


if __name__ == "__main__":
    validate()
    print("python foundation: valid")
