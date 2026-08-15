from __future__ import annotations

from collections.abc import Sequence

from app.analysis_modules.base import AnalysisModule


DEFAULT_MINIMUM_DOMAIN_SCORE = 0.5


class ModuleRegistry:
    """Select a domain module deterministically, with GenericModule as fallback."""

    def __init__(
        self,
        modules: Sequence[AnalysisModule],
        minimum_domain_score: float = DEFAULT_MINIMUM_DOMAIN_SCORE,
    ) -> None:
        self._modules = tuple(modules)
        self.minimum_domain_score = minimum_domain_score
        self._fallback_module = next(
            (module for module in self._modules if module.is_fallback),
            None,
        )
        if self._fallback_module is None:
            raise ValueError("ModuleRegistry requires one fallback module.")

    def select_module(self, available_fields: set[str]) -> AnalysisModule:
        fields = {str(field) for field in available_fields}
        selected: AnalysisModule | None = None
        selected_score = self.minimum_domain_score

        for module in self._modules:
            if module.is_fallback:
                continue
            score = module.match_score(fields)
            if score > selected_score:
                selected = module
                selected_score = score

        return selected or self._fallback_module
