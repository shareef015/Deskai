from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Evidence, Incident, RunContext
from .prompt_security import PromptInjectionFirewall


@dataclass(frozen=True, slots=True)
class CorpusChunk:
    document_id: str
    chunk_id: str
    tenant_id: str
    text: str
    tags: frozenset[str]
    trusted: bool = False


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    evidence: tuple[Evidence, ...]
    blocked_chunks: tuple[str, ...]


class GovernedRetriever:
    def __init__(self, chunks: Iterable[CorpusChunk], firewall: PromptInjectionFirewall | None = None) -> None:
        self._chunks = tuple(chunks)
        self._firewall = firewall or PromptInjectionFirewall()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token.strip(".,:;!?()[]{}\"'").lower() for token in text.split() if len(token) > 2}

    def retrieve(self, context: RunContext, incident: Incident, *, limit: int = 5) -> RetrievalResult:
        context.require_tenant(incident.tenant_id)
        query_tokens = self._tokens(f"{incident.title} {incident.description} {incident.domain.value}")
        scored: list[tuple[float, CorpusChunk]] = []
        blocked: list[str] = []
        for chunk in self._chunks:
            if chunk.tenant_id != context.tenant_id:
                continue
            inspection = self._firewall.inspect(chunk.text)
            if not inspection.allowed:
                blocked.append(chunk.chunk_id)
                continue
            overlap = len(query_tokens.intersection(self._tokens(chunk.text)))
            tag_bonus = 2 if incident.domain.value in chunk.tags else 0
            score = float(overlap + tag_bonus)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: (-pair[0], pair[1].document_id, pair[1].chunk_id))
        evidence = tuple(
            Evidence(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                tenant_id=chunk.tenant_id,
                text=chunk.text,
                score=score,
                trusted=chunk.trusted,
            )
            for score, chunk in scored[:limit]
        )
        return RetrievalResult(evidence=evidence, blocked_chunks=tuple(blocked))
