from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class PromptInspection:
    allowed: bool
    reasons: tuple[str, ...]


class PromptInjectionFirewall:
    """Treat retrieved text as untrusted data and flag instruction-like payloads."""

    _patterns = tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"system\s+prompt",
            r"developer\s+message",
            r"reveal\s+.*secret",
            r"exfiltrat(e|ion)",
            r"disable\s+(guardrail|safety|policy)",
            r"call\s+.*tool\s+without\s+approval",
            r"bypass\s+.*approval",
        )
    )

    def inspect(self, text: str) -> PromptInspection:
        reasons = tuple(pattern.pattern for pattern in self._patterns if pattern.search(text))
        return PromptInspection(allowed=not reasons, reasons=reasons)

    def safe_excerpt(self, text: str, *, max_chars: int = 1200) -> str:
        inspected = self.inspect(text)
        if not inspected.allowed:
            return "[UNTRUSTED_RETRIEVED_INSTRUCTIONS_BLOCKED]"
        return text[:max_chars]
