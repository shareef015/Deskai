import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> None:
    contract = json.loads((ROOT / "contracts/repository-boundaries.json").read_text())
    assert contract["single_root"] == "deskpilot-ai"
    required = list(contract["deployables"].values()) + contract["shared_packages"]
    required += contract["operational_roots"]
    missing = [path for path in required if not (ROOT / path).is_dir()]
    assert not missing, f"missing repository roots: {missing}"
    assert "endpoint_execution_is_available_only_through_mcp_gateway" in contract["rules"]


if __name__ == "__main__":
    validate()
    print("repository structure: valid")
