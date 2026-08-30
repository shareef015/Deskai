from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .models import Citation, Evidence, RunContext


class CitationIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GroundingBundle:
    evidence: tuple[Evidence, ...]
    citations: tuple[Citation, ...]


class CitationVerifier:
    def build(self, context: RunContext, evidence: Iterable[Evidence]) -> GroundingBundle:
        rows = tuple(evidence)
        if not rows:
            raise CitationIntegrityError("no_grounding_evidence")
        seen: set[tuple[str, str]] = set()
        citations: list[Citation] = []
        for item in rows:
            context.require_tenant(item.tenant_id)
            key = (item.document_id, item.chunk_id)
            if key in seen:
                raise CitationIntegrityError("duplicate_citation")
            seen.add(key)
            citation = item.citation
            expected = sha256(item.text.encode("utf-8")).hexdigest()
            if citation.content_hash != expected:
                raise CitationIntegrityError("citation_hash_mismatch")
            citations.append(citation)
        return GroundingBundle(rows, tuple(citations))
