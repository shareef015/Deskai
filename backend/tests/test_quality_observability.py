from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_llmops.adapters import langsmith_trace_metadata, to_otel_envelope
from deskpilot_llmops.metrics import MetricRegistry
from deskpilot_llmops.models import TraceContext
from deskpilot_llmops.redaction import redact_value
from deskpilot_llmops.telemetry import TelemetryRecorder


class ObservabilityContractTests(unittest.TestCase):
    def test_trace_context_is_stable_and_w3c_shaped(self) -> None:
        ctx = TraceContext.root(correlation_id="corr-1", tenant_id="tenant-a", run_id="run-1")
        self.assertEqual(len(ctx.trace_id), 32)
        self.assertEqual(len(ctx.span_id), 16)
        self.assertEqual(len(ctx.traceparent.split("-")), 4)
        self.assertEqual(ctx, TraceContext.root(correlation_id="corr-1", tenant_id="tenant-a", run_id="run-1"))

    def test_child_span_preserves_trace(self) -> None:
        root = TraceContext.root(correlation_id="c", tenant_id="t", run_id="r")
        child = root.child("rag", 1)
        self.assertEqual(root.trace_id, child.trace_id)
        self.assertNotEqual(root.span_id, child.span_id)

    def test_metric_registry_rejects_high_cardinality_labels(self) -> None:
        metrics = MetricRegistry()
        with self.assertRaises(ValueError):
            metrics.record("deskpilot.test", 1, labels={"user_id": "u1"})

    def test_metric_registry_accepts_governed_low_cardinality_labels(self) -> None:
        metrics = MetricRegistry()
        metrics.record("deskpilot.rag.requests", 1, unit="{request}", labels={"stage": "rag", "status": "ok"})
        self.assertEqual(metrics.latest("deskpilot.rag.requests"), 1.0)

    def test_redaction_strips_tokens_and_email(self) -> None:
        value = redact_value({"access_token": "abc", "message": "Bearer secret-token user@example.com"})
        self.assertEqual(value["access_token"], "[REDACTED]")
        self.assertNotIn("user@example.com", str(value))
        self.assertNotIn("secret-token", str(value))

    def test_span_and_log_share_trace_identity(self) -> None:
        telemetry = TelemetryRecorder()
        root = telemetry.root_context(correlation_id="corr", tenant_id="tenant", run_id="run")
        child = telemetry.record_span(root, name="retrieve", stage="rag", started_at=1.0, ended_at=1.1)
        telemetry.log(child, timestamp=1.1, severity="INFO", event_name="retrieved", message="done")
        self.assertEqual(telemetry.spans[0].trace_id, telemetry.logs[0].trace_id)
        self.assertEqual(telemetry.logs[0].correlation_id, "corr")

    def test_otel_adapter_contains_genai_operation_attribute(self) -> None:
        telemetry = TelemetryRecorder()
        root = telemetry.root_context(correlation_id="corr", tenant_id="tenant", run_id="run")
        telemetry.record_span(root, name="route", stage="langgraph", started_at=1.0, ended_at=1.01)
        env = to_otel_envelope(telemetry.spans[0])
        self.assertEqual(env.attributes["gen_ai.operation.name"], "invoke_workflow")

    def test_langsmith_metadata_supports_release_correlation(self) -> None:
        meta = langsmith_trace_metadata(tenant_id="tenant-a", correlation_id="corr", environment="staging", release="v1")
        self.assertEqual(meta["metadata"]["correlation_id"], "corr")
        self.assertIn("staging", meta["tags"])


if __name__ == "__main__":
    unittest.main()

class LlmObservationTests(unittest.TestCase):
    def test_incoming_traceparent_continues_browser_trace(self) -> None:
        incoming = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
        ctx = TraceContext.from_traceparent(traceparent=incoming, correlation_id="corr", tenant_id="t", run_id="r")
        self.assertEqual(ctx.trace_id, "0123456789abcdef0123456789abcdef")
        self.assertTrue(ctx.sampled)

    def test_invalid_all_zero_traceparent_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TraceContext.from_traceparent(traceparent="00-00000000000000000000000000000000-0000000000000000-01", correlation_id="c", tenant_id="t", run_id="r")

    def test_llm_observer_keeps_raw_prompt_out_of_telemetry(self) -> None:
        from deskpilot_llmops.costs import CostLedger, ModelPriceProfile
        from deskpilot_llmops.llm import LlmCallObserver
        telemetry = TelemetryRecorder()
        root = telemetry.root_context(correlation_id="corr", tenant_id="t", run_id="r")
        observer = LlmCallObserver(telemetry, CostLedger([ModelPriceProfile("synthetic", 1.0, 2.0)]))
        observer.record(root, model_family="synthetic", prompt="private prompt", response="private answer", input_tokens=100, output_tokens=50, latency_ms=20, started_at=1)
        self.assertNotIn("private prompt", str(telemetry.spans[0].attributes))
        self.assertNotIn("private answer", str(telemetry.spans[0].attributes))
        self.assertEqual(len(telemetry.spans[0].attributes["deskpilot.prompt.fingerprint"]), 64)
