"""Load the synthetic knowledge base into governed retrieval corpus chunks.

The JSON corpus at ``data/synthetic/knowledge-base.json`` is the grounding source
for the RAG pipeline. This module turns it into :class:`CorpusChunk` values that
:class:`GovernedRetriever` can score, and re-verifies each chunk's content hash so
a tampered corpus is rejected before it can be retrieved.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from .retrieval import CorpusChunk

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_PATH = _REPO_ROOT / "data" / "synthetic" / "knowledge-base.json"


class KnowledgeBaseIntegrityError(RuntimeError):
    """Raised when the corpus fails its own hash or structure checks."""


def _verify(corpus: dict[str, Any]) -> dict[str, Any]:
    if not corpus.get("synthetic_only", False):
        raise KnowledgeBaseIntegrityError("corpus is not marked synthetic_only")
    for article in corpus["articles"]:
        for chunk in article["chunks"]:
            expected = sha256(chunk["text"].encode("utf-8")).hexdigest()
            if chunk["content_sha256"] != expected:
                raise KnowledgeBaseIntegrityError(f"content hash mismatch in {article['id']}:{chunk['chunk_id']}")
    return corpus


def load_knowledge_base(path: Path | str = DEFAULT_CORPUS_PATH) -> dict[str, Any]:
    return _verify(json.loads(Path(path).read_text(encoding="utf-8")))


def as_corpus_chunks(
    corpus: dict[str, Any] | None = None,
    *,
    tenant_id: str | None = None,
    path: Path | str = DEFAULT_CORPUS_PATH,
) -> tuple[CorpusChunk, ...]:
    """Return the corpus as retrieval chunks bound to a tenant.

    ``tenant_id`` defaults to the tenant recorded in the corpus. Passing a
    different value rebinds every chunk to that tenant so the same synthetic
    corpus can back more than one demo tenant without leaking across them.
    """

    corpus = _verify(corpus) if corpus is not None else load_knowledge_base(path)
    bound_tenant = tenant_id or corpus["tenant_id"]
    chunks: list[CorpusChunk] = []
    for article in corpus["articles"]:
        tags = frozenset(article["tags"])
        for chunk in article["chunks"]:
            chunks.append(
                CorpusChunk(
                    document_id=article["id"],
                    chunk_id=f"{article['id']}:{chunk['chunk_id']}",
                    tenant_id=bound_tenant,
                    text=chunk["text"],
                    tags=tags,
                    trusted=bool(article.get("trusted", True)),
                )
            )
    return tuple(chunks)
