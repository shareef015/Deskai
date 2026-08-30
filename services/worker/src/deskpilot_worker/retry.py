from __future__ import annotations

import secrets


def retry_delay_seconds(attempt: int, *, base: int = 2, maximum: int = 900) -> float:
    if attempt < 1:
        raise ValueError("attempt must be positive")
    ceiling = min(maximum, base * (2 ** (attempt - 1)))
    return secrets.randbelow(ceiling * 1000 + 1) / 1000
