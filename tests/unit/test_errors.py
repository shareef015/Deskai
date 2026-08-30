from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/python/deskpilot-core/src"))
from deskpilot_core.errors import DeskPilotError, ErrorCode, problem_document, unexpected_problem  # noqa: E402


class ErrorTests(unittest.TestCase):
    def test_expected_error_maps_to_stable_problem(self):
        error = DeskPilotError(ErrorCode.RESOURCE_NOT_FOUND, "The requested incident does not exist.")
        problem = problem_document(error, "corr-1")
        self.assertEqual(problem["status"], 404)
        self.assertEqual(problem["code"], "resource_not_found")
        self.assertFalse(problem["retryable"])

    def test_retryable_failure_has_bounded_guidance(self):
        error = DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE, retry_after_seconds=30)
        problem = problem_document(error, "corr-2")
        self.assertTrue(problem["retryable"])
        self.assertEqual(problem["retry_after_seconds"], 30)
        with self.assertRaises(ValueError):
            DeskPilotError(ErrorCode.RATE_LIMITED, retry_after_seconds=7200)

    def test_unsafe_detail_is_rejected(self):
        with self.assertRaises(ValueError):
            DeskPilotError(ErrorCode.CONFLICT, "token=abc@example.com")

    def test_unexpected_problem_never_contains_exception_detail(self):
        problem = unexpected_problem("corr-3")
        encoded = str(problem)
        self.assertEqual(problem["code"], "internal_error")
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("detail", problem)

