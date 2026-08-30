from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GoldenCase:
    case_id: str
    domain: str
    query: str
    expected_route: str
    expected_tool: str
    relevant_chunk_ids: frozenset[str]
    required_citations: int
    should_block_injection: bool
    expected_final_state: str


class GoldenDataset:
    def __init__(self, cases: list[GoldenCase]) -> None:
        ids = [c.case_id for c in cases]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_golden_case_id")
        if not cases:
            raise ValueError("golden_dataset_empty")
        self.cases = tuple(cases)

    @classmethod
    def load(cls, path: str | Path) -> "GoldenDataset":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("schema_version") != 1:
            raise ValueError("unsupported_golden_dataset_schema")
        rows = []
        for item in raw.get("cases", []):
            rows.append(GoldenCase(
                case_id=str(item["case_id"]), domain=str(item["domain"]), query=str(item["query"]),
                expected_route=str(item["expected_route"]), expected_tool=str(item["expected_tool"]),
                relevant_chunk_ids=frozenset(str(x) for x in item["relevant_chunk_ids"]),
                required_citations=int(item["required_citations"]), should_block_injection=bool(item["should_block_injection"]),
                expected_final_state=str(item["expected_final_state"]),
            ))
        return cls(rows)
