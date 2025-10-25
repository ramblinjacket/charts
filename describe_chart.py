from __future__ import annotations

import json
from typing import Any, Dict, List

from chart_payloads import (
    ChartPayloadError,
    build_editable_fields,
    extract_chart_options,
    load_chart_payload,
    summarize_options,
)
from skill_runtime import SkillInput, SkillOutput, SkillParameter, skill


@skill(
    name="Describe Chart",
    description="Summarize an existing Highcharts payload and highlight editable properties.",
    parameters=[
        SkillParameter(
            name="saved_payload_id",
            description="Identifier returned when the chart payload was stored in skill memory.",
            required=True,
        )
    ],
)
def describe_chart(parameters: SkillInput) -> SkillOutput:
    saved_payload_id = getattr(parameters.arguments, "saved_payload_id", None)
    if not saved_payload_id:
        return SkillOutput(final_prompt="A saved payload ID is required to describe a chart.")

    try:
        payload = load_chart_payload(saved_payload_id)
        options = extract_chart_options(payload)
        summary = summarize_options(options)
    except ChartPayloadError as exc:
        return SkillOutput(final_prompt=str(exc))

    editable_fields = build_editable_fields(options)
    summary_text = [
        f"Chart type: {summary['chart_type']}",
        f"Series count: {summary['series_count']}",
    ]
    for serie in summary.get("series", []):
        summary_text.append(
            f"Series {serie['index']} ({serie['name']}): color={serie['color'] or 'default'}, dashStyle={serie['dashStyle'] or 'solid'}"
        )

    narrative = "\n".join(summary_text)
    final_payload = {
        "summary": summary,
        "editable_fields": editable_fields,
        "chart_options": options,
    }

    return SkillOutput(
        final_prompt=json.dumps(final_payload, indent=2),
        narrative=narrative,
    )
