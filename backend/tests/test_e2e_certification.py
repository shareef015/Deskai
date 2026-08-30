from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_e2e.certification import build_final_report
from deskpilot_e2e.personas import DemoPersonaError, DemoPersonaRegistry
from deskpilot_e2e.reset import DemoResetController, state_fingerprint
from deskpilot_e2e.runner import RecruiterDemoRunner, service_desk_script
from deskpilot_e2e.scenarios import GOLDEN_DEMO_SCENARIOS


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class EndToEndCertificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = DemoPersonaRegistry()
        self.persona = self.registry.select("service-desk-demo", demo_mode=True, requested_tenant="tenant-a")

    def test_demo_personas_are_demo_mode_only(self) -> None:
        with self.assertRaises(DemoPersonaError):
            self.registry.select("service-desk-demo", demo_mode=False)

    def test_demo_persona_cannot_be_rebound_to_foreign_tenant(self) -> None:
        with self.assertRaises(DemoPersonaError):
            self.registry.select("service-desk-demo", demo_mode=True, requested_tenant="tenant-b")

    def test_service_desk_script_contains_greeting_and_intake_question(self) -> None:
        script = service_desk_script()
        self.assertTrue(script.greeting.startswith("Hi"))
        self.assertIn("How can I help", script.intake_question)
        self.assertIn("approval", script.permission_prompt.lower())

    def test_all_golden_demo_scenarios_pass(self) -> None:
        runner = RecruiterDemoRunner()
        results = [runner.run(self.persona, scenario) for scenario in GOLDEN_DEMO_SCENARIOS]
        self.assertEqual(len(results), 6)
        self.assertTrue(all(result.passed for result in results), [(r.scenario_id, r.final_state, r.notes) for r in results])

    def test_printer_and_outlook_domains_are_both_covered(self) -> None:
        domains = {scenario.domain for scenario in GOLDEN_DEMO_SCENARIOS}
        self.assertEqual(domains, {"printer", "outlook"})

    def test_verification_failure_never_false_closes(self) -> None:
        scenario = next(s for s in GOLDEN_DEMO_SCENARIOS if s.scenario_id == "DEMO-VERIFY-FAIL")
        result = RecruiterDemoRunner().run(self.persona, scenario)
        self.assertTrue(result.passed)
        self.assertEqual(result.final_state, "diagnosing")
        self.assertNotIn("incident_closed", result.event_types)

    def test_cross_tenant_demo_scenario_is_denied_before_retrieval(self) -> None:
        scenario = next(s for s in GOLDEN_DEMO_SCENARIOS if s.scenario_id == "DEMO-CROSS-TENANT")
        result = RecruiterDemoRunner().run(self.persona, scenario)
        self.assertTrue(result.passed)
        self.assertEqual(result.final_state, "denied")
        self.assertEqual(result.citation_count, 0)

    def test_demo_reset_restores_deterministic_baseline(self) -> None:
        reset = DemoResetController()
        baseline = reset.baseline_fingerprint
        reset.mutate(scenario="x", incident_id="i", device_id="d", fault="f", persona_id="p")
        self.assertNotEqual(state_fingerprint(reset.state), baseline)
        result = reset.reset()
        self.assertTrue(result.restored)
        self.assertEqual(result.after, baseline)

    def test_final_release_blocker_report_passes_when_all_gates_pass(self) -> None:
        reset = DemoResetController()
        runner = RecruiterDemoRunner(reset=reset)
        results = tuple(runner.run(self.persona, scenario) for scenario in GOLDEN_DEMO_SCENARIOS)
        reset_result = reset.reset()
        report = build_final_report(
            project_root=PROJECT_ROOT,
            scenario_results=results,
            reset_verified=reset_result.restored,
            contract_passed=True,
            accessibility_passed=True,
            failure_recovery_passed=True,
        )
        self.assertTrue(report.passed, report.blockers)
        self.assertEqual(report.blockers, ())
        self.assertTrue(report.fingerprint)

    def test_final_release_blocker_report_blocks_failed_contract(self) -> None:
        report = build_final_report(
            project_root=PROJECT_ROOT,
            scenario_results=(),
            reset_verified=True,
            contract_passed=False,
            accessibility_passed=True,
            failure_recovery_passed=True,
        )
        self.assertFalse(report.passed)
        self.assertIn("gate:frontend_backend_contracts", report.blockers)


if __name__ == "__main__":
    unittest.main()
