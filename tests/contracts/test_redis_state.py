from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("redis_validator", ROOT / "scripts/validate_redis_state.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/redis-state-policy.json").read_text())

KEY_SPEC = importlib.util.spec_from_file_location(
    "redis_keys", ROOT / "packages/python/deskpilot-core/src/deskpilot_core/redis_keys.py"
)
assert KEY_SPEC and KEY_SPEC.loader
KEYS = importlib.util.module_from_spec(KEY_SPEC)
sys.modules[KEY_SPEC.name] = KEYS
KEY_SPEC.loader.exec_module(KEYS)


class RedisStateTests(unittest.TestCase):
    def test_redis_state_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_tenants_receive_distinct_namespaces(self):
        keyspace = KEYS.RedisKeyspace(b"k" * 32)
        first = keyspace.key(UUID(int=1), "cache", "incident")
        second = keyspace.key(UUID(int=2), "cache", "incident")
        self.assertNotEqual(first, second)

    def test_raw_tenant_id_is_not_in_key(self):
        tenant = UUID("00000000-0000-0000-0000-000000000001")
        key = KEYS.RedisKeyspace(b"k" * 32).key(tenant, "cache", "incident")
        self.assertNotIn(str(tenant), key)

    def test_sessions_fail_closed(self):
        self.assertEqual(POLICY["failure_modes"]["session_unavailable"], "fail_closed_503")

    def test_lock_ttl_is_bounded(self):
        self.assertEqual(POLICY["ttl_seconds"]["distributed_lock_maximum"], 120)
