import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> None:
    api = json.loads((ROOT / "contracts/openapi/deskpilot-v1.json").read_text())
    schemas = api["components"]["schemas"]
    assert api["openapi"] == "3.1.0" and api["servers"][0]["url"] == "/api/v1"
    assert set(schemas["CreateConversationRequest"]["required"]) == {"device_id", "initial_message"}
    assert schemas["ConsentRequest"]["properties"]["scope"]["enum"] == ["diagnostic", "remediation", "remote_session"]
    operation_ids = {op["operationId"] for path in api["paths"].values() for op in path.values()}
    assert operation_ids == {"createConversation", "sendMessage", "recordConsent"}


if __name__ == "__main__":
    validate()
    print("shared schemas: valid")
