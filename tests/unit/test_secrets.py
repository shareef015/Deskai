from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/python/deskpilot-core/src"))

from deskpilot_core.secrets import (  # noqa: E402
    EnvironmentSecretProvider,
    FileSecretProvider,
    RotationMetadata,
    SecretReference,
    SecretResolutionError,
    SecretResolver,
    SecretValue,
)


class SecretTests(unittest.TestCase):
    def test_value_and_reference_are_redacted(self):
        self.assertNotIn("actual-value", repr(SecretValue("actual-value")))
        self.assertEqual(str(SecretReference.parse("env://DATABASE_PASSWORD")), "env://[REDACTED]")

    def test_environment_resolution_and_missing_secret_fail_closed(self):
        resolver = SecretResolver({"env": EnvironmentSecretProvider({"TOKEN": "value"})})
        self.assertEqual(resolver.resolve("env://TOKEN").reveal(), "value")
        with self.assertRaises(SecretResolutionError):
            resolver.resolve("env://MISSING")

    def test_file_provider_enforces_approved_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = root / "database"
            secret.write_text("runtime-only", encoding="utf-8")
            provider = FileSecretProvider((root,))
            self.assertEqual(provider.resolve(SecretReference.parse(f"file://{secret}")).reveal(), "runtime-only")
            with self.assertRaises(SecretResolutionError):
                provider.resolve(SecretReference.parse("file:///etc/passwd"))

    def test_unapproved_scheme_and_expired_rotation_are_rejected(self):
        with self.assertRaises(SecretResolutionError):
            SecretReference.parse("http://example.invalid/secret")
        now = datetime.now(UTC)
        metadata = RotationMetadata("database", "v1", now - timedelta(days=2), now - timedelta(seconds=1))
        with self.assertRaises(SecretResolutionError):
            metadata.validate(now=now)

