from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "src"))

SPEC = importlib.util.spec_from_file_location(
    "knowledge_base_validator", ROOT / "scripts/validate_knowledge_base.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

from deskpilot_ai_pipeline.knowledge_base import (  # noqa: E402
    KnowledgeBaseIntegrityError,
    as_corpus_chunks,
    load_knowledge_base,
)
from deskpilot_ai_pipeline.models import (  # noqa: E402
    Incident,
    IncidentDomain,
    RunContext,
)
from deskpilot_ai_pipeline.retrieval import GovernedRetriever  # noqa: E402

TENANT = "tenant-demo-kw"


def _context(tenant: str = TENANT) -> RunContext:
    return RunContext(
        run_id="run-kb",
        tenant_id=tenant,
        user_id="user-kb",
        session_id="sess-kb",
        capabilities=frozenset({"ai:diagnose"}),
        started_at=0.0,
        deadline_at=1_000.0,
        correlation_id="corr-kb",
    )


class KnowledgeBaseContractTests(unittest.TestCase):
    def test_corpus_and_policy_valid(self) -> None:
        self.assertEqual(V.validate(), [])

    def test_loader_binds_every_chunk_to_the_tenant(self) -> None:
        corpus = load_knowledge_base()
        chunks = as_corpus_chunks(corpus)
        self.assertEqual(len(chunks), corpus["chunk_count"])
        self.assertTrue(all(chunk.tenant_id == TENANT for chunk in chunks))
        self.assertTrue(all(chunk.trusted for chunk in chunks))

    def test_loader_can_rebind_to_another_tenant(self) -> None:
        chunks = as_corpus_chunks(tenant_id="tenant-other-demo")
        self.assertTrue(all(chunk.tenant_id == "tenant-other-demo" for chunk in chunks))

    def test_tampered_chunk_is_rejected(self) -> None:
        corpus = load_knowledge_base()
        corpus["articles"][0]["chunks"][0]["text"] += " tampered"
        with self.assertRaises(KnowledgeBaseIntegrityError):
            as_corpus_chunks(corpus)

    def test_retrieval_grounds_an_outlook_incident_in_the_corpus(self) -> None:
        retriever = GovernedRetriever(as_corpus_chunks())
        incident = Incident(
            incident_id="INC-KB-1",
            tenant_id=TENANT,
            domain=IncidentDomain.OUTLOOK,
            title="Outlook shows Disconnected",
            description="Outlook for Windows keeps dropping the connection and will not send mail.",
            device_id="WIN11-03",
        )
        result = retriever.retrieve(_context(), incident, limit=5)
        self.assertTrue(result.evidence)
        self.assertTrue(all(ev.document_id.startswith("KB-") for ev in result.evidence))
        self.assertTrue(any("connect" in ev.document_id.lower() for ev in result.evidence))

    def test_retrieval_denies_a_cross_tenant_context(self) -> None:
        retriever = GovernedRetriever(as_corpus_chunks())
        incident = Incident(
            incident_id="INC-KB-2",
            tenant_id="tenant-demo-kw",
            domain=IncidentDomain.PRINTER,
            title="Printer offline",
            description="The printer shows offline on one device only.",
            device_id="WIN11-04",
        )
        with self.assertRaises(PermissionError):
            retriever.retrieve(_context("tenant-intruder"), incident, limit=5)


if __name__ == "__main__":
    unittest.main()
