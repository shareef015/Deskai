from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from deskpilot_ai_pipeline.prompt_security import PromptInjectionFirewall
from deskpilot_ai_pipeline.retrieval import CorpusChunk


class PoisonedKnowledgeViolation(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class KnowledgeProvenance:
    document_id: str
    chunk_id: str
    tenant_id: str
    content_sha256: str
    trusted_source: bool
    approved_for_retrieval: bool


class KnowledgeIntegrityGate:
    def __init__(self, firewall: PromptInjectionFirewall | None = None) -> None:
        self._firewall = firewall or PromptInjectionFirewall()

    @staticmethod
    def fingerprint(text: str) -> str:
        return sha256(text.encode()).hexdigest()

    def validate(self, chunk: CorpusChunk, provenance: KnowledgeProvenance) -> None:
        if (chunk.document_id, chunk.chunk_id, chunk.tenant_id) != (
            provenance.document_id,
            provenance.chunk_id,
            provenance.tenant_id,
        ):
            raise PoisonedKnowledgeViolation("provenance_binding_mismatch")
        if self.fingerprint(chunk.text) != provenance.content_sha256:
            raise PoisonedKnowledgeViolation("content_integrity_mismatch")
        if not provenance.trusted_source or not provenance.approved_for_retrieval:
            raise PoisonedKnowledgeViolation("unapproved_knowledge_source")
        if not self._firewall.inspect(chunk.text).allowed:
            raise PoisonedKnowledgeViolation("instruction_like_retrieval_payload")
