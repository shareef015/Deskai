import sys
import unittest
from datetime import UTC
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/python/deskpilot-core/src"))

from deskpilot_core import Result, SystemClock, new_correlation_id  # noqa: E402


class CoreTests(unittest.TestCase):
    def test_correlation_ids_are_unique(self):
        self.assertNotEqual(new_correlation_id(), new_correlation_id())

    def test_clock_is_timezone_aware(self):
        self.assertEqual(SystemClock().now().tzinfo, UTC)

    def test_success_result(self):
        self.assertTrue(Result(value={"status": "ok"}).is_ok)

    def test_ambiguous_result_is_rejected(self):
        with self.assertRaises(ValueError):
            Result(value="ok", error="failed")


if __name__ == "__main__":
    unittest.main()
