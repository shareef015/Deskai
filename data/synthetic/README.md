# Synthetic data

Deterministic, non-personal fixtures for demonstrations, tests and offline evaluation.

Each `generate_*.py` script reads its contract inputs, builds a canonical
(`sort_keys`, compact) JSON payload, and seals it with a SHA-256 digest. Re-running a
generator on the same inputs produces byte-identical output.

## Knowledge base (RAG grounding corpus)

`knowledge-base.json` is the corpus the governed RAG pipeline retrieves from to
produce grounded, cited answers.

| File | Role |
|---|---|
| `knowledge-base.articles.json` | Editable article content: title, symptoms, and the ordered troubleshooting chunks |
| `generate_knowledge_base.py` | Resolves each citation against the registered knowledge-source contracts, hashes every chunk, writes the sealed corpus |
| `knowledge-base.json` | Generated corpus — 30 articles / 150 chunks across `outlook`, `printer`, `scanner`, `windows_network` |
| `contracts/knowledge-base-policy.json` | The corpus contract (coverage, citation, safety, digest rules) |
| `scripts/validate_knowledge_base.py` | Validator: digests, citations, per-domain coverage, content hashes, safety and de-identification checks |
| `backend/src/deskpilot_ai_pipeline/knowledge_base.py` | Loader → tenant-bound `CorpusChunk`s for `GovernedRetriever`; re-verifies content hashes |

Every article maps to a support-catalogue incident, carries a Windows 10/11 servicing
scope, and cites exactly one registered Microsoft source. Every chunk follows the
product lifecycle: confirm scope → read-only checks → evidence-based causes →
approval-gated remediation with rollback → technical and employee verification. The
corpus never contains credential-extraction, arbitrary-shell, or hidden-remote-access
guidance.

```bash
python data/synthetic/generate_knowledge_base.py     # regenerate after editing articles
python scripts/validate_knowledge_base.py            # validate the corpus + policy
python -m unittest tests.contracts.test_knowledge_base
```
