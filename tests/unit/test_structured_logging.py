from __future__ import annotations

import json
import logging
import sys
import unittest
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/python/deskpilot-core/src"))
from deskpilot_core.structured_logging import (  # noqa: E402
    JsonLogFormatter,
    LogContext,
    LoggingContractError,
    build_log_event,
    emit,
)


class StructuredLoggingTests(unittest.TestCase):
    def test_event_has_required_utc_context_and_hashed_tenant(self):
        event = build_log_event(
            "info", "incident.created",
            LogContext("corr-1", "api", "test", tenant_id="tenant-a", incident_id="inc-1"),
            now=datetime(2026, 8, 26, tzinfo=UTC), tenant_salt="deployment-salt",
        )
        self.assertEqual(event["timestamp"], "2026-08-26T00:00:00Z")
        self.assertNotIn("tenant_id", event)
        self.assertEqual(len(event["tenant_key"]), 24)

    def test_recursive_redaction_masks_secrets_bearer_and_email(self):
        event = build_log_event(
            "warning", "auth.failed", LogContext("corr-2", "api", "test"),
            {"password": "value", "nested": {"Authorization": "Bearer abc.def", "user": "a@example.com"}},
        )
        encoded = json.dumps(event)
        self.assertNotIn("value", encoded)
        self.assertNotIn("abc.def", encoded)
        self.assertNotIn("a@example.com", encoded)

    def test_missing_context_and_invalid_event_fail_closed(self):
        with self.assertRaises(LoggingContractError):
            build_log_event("info", "bad event", LogContext("", "api", "test"))

    def test_formatter_emits_one_json_object(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonLogFormatter())
        logger = logging.getLogger("deskpilot-test-structured")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)
        payload = build_log_event("info", "service.ready", LogContext("corr-3", "api", "test"))
        emit(logger, payload)
        parsed = json.loads(stream.getvalue())
        self.assertEqual(parsed["event"], "service.ready")

