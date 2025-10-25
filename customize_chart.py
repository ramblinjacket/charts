from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from chart_instruction_parser import instructions_to_updates
from chart_payloads import (
    ChartPayloadError,
    append_history_entry,
    extract_chart_options,
    get_nested_value,
    load_chart_payload,
    persist_chart_payload,
    set_nested_value,
    tokenize_path,
    validate_update_path,
)
from skill_runtime import SkillInput, SkillOutput, SkillParameter, skill


def _parse_key_value_lines(raw: str) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        path, value = stripped.split("=", 1)
        path = path.strip()
        value = value.strip()
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value
        updates.append({"path": path, "value": parsed_value})
    return updates


def _normalize_updates(raw_updates: Any) -> List[Dict[str, Any]]:
    if raw_updates is None:
        return []

    data = raw_updates
    if isinstance(raw_updates, str):
        raw_updates = raw_updates.strip()
        if not raw_updates:
            return []
        try:
            data = json.loads(raw_updates)
        except json.JSONDecodeError:
            data = _parse_key_value_lines(raw_updates)
    if isinstance(data, Mapping):
        return [{"path": path, "value": value} for path, value in data.items()]
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        normalized: List[Dict[str, Any]] = []
        for item in data:
            if isinstance(item, Mapping) and "path" in item and "value" in item:
                normalized.append({"path": item["path"], "value": item["value"]})
            elif isinstance(item, Sequence) and len(item) == 2:
                normalized.append({"path": item[0], "value": item[1]})
        return normalized
    return []


@skill(
    name="Customize Chart",
    description="Apply structured Highcharts option updates to a saved payload.",
    parameters=[
        SkillParameter(
            name="saved_payload_id",
            description="Identifier returned when the chart payload was saved.",
            required=True,
        ),
        SkillParameter(
            name="updates",
            description="JSON or key=value list describing chart option updates (e.g. {\"series[0].color\": \"#ff0000\"}).",
            required=False,
        ),
        SkillParameter(
            name="instructions",
            description="Optional natural language instructions (used for history/context).",
            required=False,
        ),
    ],
)
def customize_chart(parameters: SkillInput) -> SkillOutput:
    args = parameters.arguments
    saved_payload_id = getattr(args, "saved_payload_id", None)
    raw_updates = getattr(args, "updates", None)
    instructions = getattr(args, "instructions", None)

    if not saved_payload_id:
        return SkillOutput(final_prompt="A saved payload ID is required to customize a chart.")

    try:
        payload = load_chart_payload(saved_payload_id)
        options = extract_chart_options(payload)
    except ChartPayloadError as exc:
        return SkillOutput(final_prompt=str(exc))

    updates = _normalize_updates(raw_updates)
    if instructions:
        auto_updates = instructions_to_updates(str(instructions), options)
        updates.extend(auto_updates)

    if not updates:
        return SkillOutput(
            final_prompt="Provide chart updates as JSON, an array of path/value pairs, key=value lines, or recognizable instructions."
        )

    chart_config = options.get("chart")
    chart_type = chart_config.get("type") if isinstance(chart_config, Mapping) else None

    change_log = []
    for update in updates:
        path = update.get("path")
        if not path:
            continue
        value = update.get("value")
        try:
            tokens = tokenize_path(path)
            validate_update_path(tokens, chart_type)
            previous = get_nested_value(options, tokens)
            set_nested_value(options, tokens, value)
        except ChartPayloadError as exc:
            return SkillOutput(final_prompt=str(exc))
        change_log.append({"path": path, "before": previous, "after": value})

    append_history_entry(
        payload,
        actor="Customize Chart",
        action="apply_updates",
        details={"instructions": instructions, "changes": change_log},
    )

    try:
        saved_id = persist_chart_payload(payload, saved_payload_id=saved_payload_id)
    except ChartPayloadError as exc:
        return SkillOutput(final_prompt=str(exc))

    narrative_lines = [f"{c['path']}: {c['before']} -> {c['after']}" for c in change_log]
    result_payload = {
        "saved_payload_id": saved_id,
        "changes": change_log,
        "chart_options": options,
    }

    return SkillOutput(
        final_prompt=json.dumps(result_payload, indent=2),
        narrative="\n".join(narrative_lines),
    )
