from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True, slots=True)
class DisclosureFinding:
    safe: bool
    reasons: tuple[str, ...]


class SensitiveOutputGuard:
    """Fail closed on common secret/token/system-prompt disclosure shapes.

    This is intentionally conservative and complements upstream data classification and
    output schema validation. It is not a substitute for DLP in production.
    """

    _patterns = tuple(
        (name, re.compile(pattern, re.IGNORECASE))
        for name, pattern in (
            ("bearer_token", r"\bbearer\s+[a-z0-9._~+\-/]+=*"),
            ("openai_key", r"\bsk-[a-z0-9_-]{16,}"),
            ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b"),
            ("private_key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            ("cookie", r"(?:session|sid|csrf|refresh)[_-]?(?:token)?\s*[:=]\s*[^\s;]{12,}"),
            ("system_prompt", r"(?:system|developer)\s+(?:prompt|message)\s*[:=]"),
            ("password_assignment", r"\bpassword\s*[:=]\s*[^\s]{8,}"),
        )
    )

    def inspect(self, text: str) -> DisclosureFinding:
        reasons = tuple(name for name, pattern in self._patterns if pattern.search(text))
        return DisclosureFinding(not reasons, reasons)

    def require_safe(self, text: str) -> str:
        finding = self.inspect(text)
        if not finding.safe:
            raise ValueError("sensitive_output_blocked:" + ",".join(finding.reasons))
        return text
