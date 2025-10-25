from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable, Iterable

try:  # pragma: no cover - prefer real framework when available
    from skill_framework import SkillVisualization  # type: ignore
except ImportError:  # pragma: no cover - fallback for local tests
    class SkillVisualization:  # type: ignore
        def __init__(self, title: str, layout: str):
            self.title = title
            self.layout = layout


try:  # pragma: no cover - prefer real framework when available
    from skill_framework.skills import SkillInput, SkillOutput, SkillParameter, skill  # type: ignore
except ImportError:  # pragma: no cover - fallback for local tests

    class SkillParameter:  # type: ignore
        def __init__(self, name: str, description: str, required: bool = False):
            self.name = name
            self.description = description
            self.required = required

    class SkillInput:  # type: ignore
        def __init__(self, arguments: Any | None = None):
            self.arguments = arguments or SimpleNamespace()

    class SkillOutput:  # type: ignore
        def __init__(
            self,
            *,
            final_prompt: str = "",
            narrative: str = "",
            visualizations: Iterable[Any] | None = None,
            export_data: Iterable[Any] | None = None,
        ) -> None:
            self.final_prompt = final_prompt
            self.narrative = narrative
            self.visualizations = list(visualizations or [])
            self.export_data = list(export_data or [])

    def skill(*_decorator_args: Any, **_decorator_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


__all__ = [
    "SkillVisualization",
    "SkillInput",
    "SkillOutput",
    "SkillParameter",
    "skill",
]
