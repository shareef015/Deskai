"""Generate the deterministic synthetic knowledge base used by the governed RAG pipeline.

Article content lives in ``knowledge-base.articles.json``. This script transforms it
into the retrieval corpus: it resolves every citation against the registered
knowledge-source contracts, hashes each chunk verbatim for citation integrity, and
writes a canonical, digest-sealed ``knowledge-base.json``.

The corpus is synthetic. It contains no real people, devices, addresses or secrets.
Each article follows the product lifecycle: confirm scope -> read-only checks ->
evidence-based causes -> approval-gated remediation with rollback -> technical and
employee verification.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("knowledge-base.articles.json")
DESTINATION = Path(__file__).with_name("knowledge-base.json")
GENERATOR_VERSION = "1.0.0"
TENANT_ID = "tenant-demo-kw"
SEED = 73001

SOURCE_CONTRACTS = (
    ROOT / "contracts/knowledge-sources.json",
    ROOT / "contracts/printer-knowledge-sources.json",
    ROOT / "contracts/scanner-knowledge-sources.json",
    ROOT / "contracts/windows-network-knowledge-sources.json",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_sources() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for path in SOURCE_CONTRACTS:
        for source in json.loads(path.read_text(encoding="utf-8"))["sources"]:
            index[source["id"]] = {
                "authority": source["authority"],
                "url": source["url"],
                "contract": path.name,
            }
    return index


def build() -> dict[str, Any]:
    definitions = json.loads(SOURCE.read_text(encoding="utf-8"))
    windows_scope = list(definitions["windows_scope"])
    sources = load_sources()
    articles: list[dict[str, Any]] = []
    chunk_total = 0

    for article in sorted(definitions["articles"], key=lambda item: item["id"]):
        source_id = article["source_id"]
        if source_id not in sources:
            raise ValueError(f"{article['id']} cites unknown source {source_id}")
        source = sources[source_id]

        chunks = []
        for position, (heading, text) in enumerate(article["chunks"].items(), start=1):
            chunks.append(
                {
                    "chunk_id": f"c{position}",
                    "heading": heading,
                    "text": text,
                    "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
            )
        chunk_total += len(chunks)

        articles.append(
            {
                "id": article["id"],
                "domain": article["domain"],
                "catalog_id": article["catalog_id"],
                "title": article["title"],
                "symptoms": list(article["symptoms"]),
                "windows_scope": windows_scope,
                "citation": {
                    "source_id": source_id,
                    "authority": source["authority"],
                    "url": source["url"],
                    "source_contract": source["contract"],
                },
                "tags": sorted({article["domain"], article["id"].split("-")[-1].lower()}),
                "trusted": True,
                "chunks": chunks,
            }
        )

    domain_counts: dict[str, int] = {}
    for article in articles:
        domain_counts[article["domain"]] = domain_counts.get(article["domain"], 0) + 1

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "synthetic_only": True,
        "generator_version": GENERATOR_VERSION,
        "tenant_id": TENANT_ID,
        "seed": SEED,
        "purpose": (
            "Grounding corpus for the governed RAG pipeline. "
            "Synthetic; no real people, devices, addresses or secrets."
        ),
        "domains": sorted(domain_counts),
        "article_count": len(articles),
        "chunk_count": chunk_total,
        "articles_per_domain": dict(sorted(domain_counts.items())),
        "source_index": {
            sid: sources[sid] for sid in sorted({a["citation"]["source_id"] for a in articles})
        },
        "articles": articles,
    }
    payload["corpus_digest"] = digest(payload)
    return payload


def canonical_bytes() -> bytes:
    body = json.dumps(build(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (body + "\n").encode()


if __name__ == "__main__":
    DESTINATION.write_bytes(canonical_bytes())
    print(DESTINATION)
