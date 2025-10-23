from __future__ import annotations

import json
from typing import Any

from answer_rocket.client import AnswerRocketClient
from skill_framework.skills import SkillInput, SkillOutput, SkillParameter, skill


def _as_json(payload: Any) -> str:
    """Convert payload objects to a JSON string suitable for the final prompt."""
    if isinstance(payload, str):
        return payload

    candidate = payload
    if hasattr(candidate, "model_dump"):
        candidate = candidate.model_dump()  # type: ignore[attr-defined]
    elif hasattr(candidate, "dict"):
        candidate = candidate.dict()  # type: ignore[call-arg]
    elif hasattr(candidate, "__dict__"):
        candidate = vars(candidate)

    try:
        return json.dumps(candidate, indent=2, sort_keys=True)
    except TypeError:
        return str(candidate)


def _as_mapping(payload: Any) -> Any:
    """Attempt to return payload as a structure suitable for visualization options."""
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload

    if hasattr(payload, "model_dump"):
        return payload.model_dump()  # type: ignore[attr-defined]
    if hasattr(payload, "dict"):
        return payload.dict()  # type: ignore[call-arg]
    if hasattr(payload, "__dict__"):
        return vars(payload)

    return payload


@skill(
    name="Display Chart",
    description="Retrieve a chart payload from skill memory and present it to the user.",
    parameters=[
        SkillParameter(
            name="saved_payload_id",
            description="Identifier returned by the Data Explorer skill when the chart was saved.",
            required=True,
        )
    ],
)
def display_chart(parameters: SkillInput) -> SkillOutput:
    saved_payload_id = getattr(parameters.arguments, "saved_payload_id", None)

    if not saved_payload_id:
        return SkillOutput(
            final_prompt="A saved payload ID is required to display the chart.",
            narrative="",
            visualizations=[],
            export_data=[],
        )

    client = AnswerRocketClient()

    try:
        payload = client.chat.get_skill_memory_payload(saved_payload_id)
    except AttributeError:
        return SkillOutput(
            final_prompt="Display Chart is unavailable because payload retrieval is not supported by this client.",
            narrative="",
            visualizations=[],
            export_data=[],
        )
    except Exception as exc:  # pragma: no cover - SDK error surface
        return SkillOutput(
            final_prompt=f"Unable to retrieve chart payload ({exc}).",
            narrative="",
            visualizations=[],
            export_data=[],
        )

    if not payload:
        return SkillOutput(
            final_prompt=f"No chart payload found for ID {saved_payload_id}.",
            narrative="",
            visualizations=[],
            export_data=[],
        )

    chart_options = _as_mapping(payload)

    visualization = {
        "title": "Display Chart",
        "layout": "standard",
        "content": {
            "type": "Document",
            "gap": "0px",
            "style": {
                "backgroundColor": "#ffffff",
                "width": "100%",
                "height": "max-content",
            },
            "children": [
                {
                    "name": "HighchartsChart0",
                    "type": "HighchartsChart",
                    "minHeight": "400px",
                    "options": chart_options,
                }
            ],
        },
    }

    return SkillOutput(
        final_prompt=_as_json(payload),
        narrative="",
        visualizations=[visualization],
        export_data=[],
    )
