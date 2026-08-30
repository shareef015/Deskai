from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    value: T | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if (self.value is None) == (self.error is None):
            raise ValueError("exactly one of value or error is required")

    @property
    def is_ok(self) -> bool:
        return self.error is None
