from __future__ import annotations

import json
from pathlib import Path


FIXTURE = Path(__file__).with_name("organization.json")


def canonical_fixture() -> bytes:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def write_fixture(destination: Path) -> None:
    """Write an exact deterministic replay without touching non-synthetic data."""
    destination.write_bytes(canonical_fixture())
