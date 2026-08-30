#!/usr/bin/env python3
"""Validate the synthetic knowledge base corpus and its policy contract."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/synthetic/knowledge-base.json"
POLICY = ROOT / "contracts/knowledge-base-policy.json"
SOURCE_CONTRACTS = (
    ROOT / "contracts/knowledge-sources.json",
    ROOT / "contracts/printer-knowledge-sources.json",
    ROOT / "contracts/scanner-knowledge-sources.json",
    ROOT / "contracts/windows-network-knowledge-sources.json",
)

DOMAINS = {"outlook", "printer", "scanner", "windows_network"}
# Guidance the product must never give. Matched case-insensitively as whole words.
FORBIDDEN = (
    "powershell",
    "cmd.exe",
    "reg add",
    "reg delete",
    "regedit",
    "extract the password",
    "extract credentials",
    "dump credentials",
    "reveal the token",
    "disable antivirus",
    "turn off defender",
    "hidden remote",
    "persistent remote",
    "unattended remote access",
)
# Any dotted-quad other than the link-local example used for APIPA is treated as a leak.
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []

    if not CORPUS.exists():
        return [f"missing corpus {CORPUS}"]
    if not POLICY.exists():
        return [f"missing policy {POLICY}"]

    corpus = _load(CORPUS)
    policy = _load(POLICY)

    known_sources: set[str] = set()
    for contract in SOURCE_CONTRACTS:
        for source in _load(contract)["sources"]:
            known_sources.add(source["id"])

    if not corpus.get("synthetic_only"):
        errors.append("corpus must set synthetic_only: true")
    if corpus.get("tenant_id") != policy.get("tenant_id"):
        errors.append("corpus tenant_id does not match policy tenant_id")

    recorded = corpus.get("corpus_digest")
    recomputed = _digest({k: v for k, v in corpus.items() if k != "corpus_digest"})
    if recorded != recomputed:
        errors.append("corpus_digest does not match corpus content")

    seen_articles: set[str] = set()
    domain_counts: dict[str, int] = {domain: 0 for domain in DOMAINS}
    chunk_total = 0

    for article in corpus.get("articles", []):
        aid = article.get("id", "<no id>")
        if aid in seen_articles:
            errors.append(f"duplicate article id {aid}")
        seen_articles.add(aid)

        domain = article.get("domain")
        if domain not in DOMAINS:
            errors.append(f"{aid}: unknown domain {domain}")
        else:
            domain_counts[domain] += 1

        if not article.get("catalog_id"):
            errors.append(f"{aid}: missing catalog_id")
        if not article.get("symptoms"):
            errors.append(f"{aid}: missing symptoms")
        if not article.get("windows_scope"):
            errors.append(f"{aid}: missing windows_scope")

        citation = article.get("citation", {})
        source_id = citation.get("source_id")
        if source_id not in known_sources:
            errors.append(f"{aid}: citation source {source_id!r} is not a registered source")
        if not citation.get("url"):
            errors.append(f"{aid}: citation has no url")

        chunks = article.get("chunks", [])
        if len(chunks) < 3:
            errors.append(f"{aid}: expected at least 3 chunks, found {len(chunks)}")
        seen_chunk_ids: set[str] = set()
        for chunk in chunks:
            chunk_total += 1
            cid = chunk.get("chunk_id", "<no id>")
            if cid in seen_chunk_ids:
                errors.append(f"{aid}:{cid}: duplicate chunk id")
            seen_chunk_ids.add(cid)

            text = chunk.get("text", "")
            if len(text) < 40:
                errors.append(f"{aid}:{cid}: chunk text too short")
            if sha256(text.encode("utf-8")).hexdigest() != chunk.get("content_sha256"):
                errors.append(f"{aid}:{cid}: content_sha256 mismatch")

            lowered = text.lower()
            for phrase in FORBIDDEN:
                if phrase in lowered:
                    errors.append(f"{aid}:{cid}: forbidden guidance {phrase!r}")
            if EMAIL.search(text):
                errors.append(f"{aid}:{cid}: contains an email address")
            for match in IPV4.findall(text):
                if not match.startswith("169.254"):
                    errors.append(f"{aid}:{cid}: contains an IP literal {match}")

    minimum = policy["coverage"]["minimum_articles_per_domain"]
    for domain, count in sorted(domain_counts.items()):
        if count < minimum:
            errors.append(f"domain {domain} has {count} articles, policy requires >= {minimum}")

    if corpus.get("article_count") != len(seen_articles):
        errors.append("article_count does not match the number of articles")
    if corpus.get("chunk_count") != chunk_total:
        errors.append("chunk_count does not match the number of chunks")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("knowledge base INVALID:")
        for error in errors:
            print(f"  - {error}")
        return 1
    corpus = _load(CORPUS)
    print(
        "knowledge base OK: "
        f"{corpus['article_count']} articles, {corpus['chunk_count']} chunks, "
        f"domains {corpus['articles_per_domain']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
