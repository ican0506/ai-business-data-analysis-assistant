from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisCapability:
    """A field-level analysis capability supplied by one domain module."""

    id: str
    name: str
    all_of: tuple[str, ...] = ()
    any_of: tuple[tuple[str, ...], ...] = ()
    description: str | None = None


class AnalysisModule(ABC):
    """Lightweight contract for a domain-specific analysis plugin."""

    id: str
    name: str
    is_fallback = False

    @abstractmethod
    def capabilities(self) -> Sequence[AnalysisCapability]:
        """Return analysis capabilities owned by this module."""

    @abstractmethod
    def match_score(self, available_fields: set[str]) -> float:
        """Return a deterministic domain confidence score in the range [0, 1]."""
