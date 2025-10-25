from __future__ import annotations

import copy
import datetime as _dt
import json
import os
from typing import Any, Dict, List, Mapping, MutableMapping, MutableSequence, Sequence, Set, Tuple

try:  # pragma: no cover - dependency provided at runtime
    from answer_rocket.client import AnswerRocketClient
except ImportError:  # pragma: no cover - fallback for unit tests
    class AnswerRocketClient:  # type: ignore[no-redef]
        def __init__(self, *_, **__):
            raise RuntimeError("AnswerRocket client is unavailable in this environment.")


class ChartPayloadError(RuntimeError):
    """Raised when chart payloads cannot be loaded or persisted."""


def _ensure_client(client: AnswerRocketClient | None = None) -> AnswerRocketClient:
    return client or AnswerRocketClient()


def _resolve_target_id(
    client: AnswerRocketClient,
    *,
    saved_payload_id: str | None = None,
    chat_entry_id: str | None = None,
) -> str:
    candidate = saved_payload_id or chat_entry_id or client._client_config.chat_entry_id or os.getenv("AR_CHAT_ENTRY_ID")
    if not candidate:
        raise ChartPayloadError("No chat entry identifier was provided.")
    return candidate


def load_chart_payload(saved_payload_id: str, *, client: AnswerRocketClient | None = None) -> Dict[str, Any]:
    if not saved_payload_id:
        raise ChartPayloadError("A saved payload ID is required.")

    client = _ensure_client(client)

    payload = client.chat.get_skill_memory_payload(saved_payload_id)
    if not payload:
        raise ChartPayloadError(f"No chart payload found for ID {saved_payload_id}.")
    if not isinstance(payload, Mapping):
        raise ChartPayloadError("Chart payloads must be JSON-like mappings.")

    return copy.deepcopy(payload)


def persist_chart_payload(
    payload: Mapping[str, Any],
    *,
    saved_payload_id: str | None = None,
    chat_entry_id: str | None = None,
    client: AnswerRocketClient | None = None,
) -> str:
    client = _ensure_client(client)
    target_id = _resolve_target_id(client, saved_payload_id=saved_payload_id, chat_entry_id=chat_entry_id)

    did_save = client.chat.set_skill_memory_payload(payload, chat_entry_id=target_id)
    if not did_save:
        raise ChartPayloadError("Chart payload could not be saved to skill memory.")

    return target_id


def extract_chart_options(payload: Mapping[str, Any]) -> MutableMapping[str, Any]:
    if "data" in payload and isinstance(payload["data"], MutableMapping):
        return payload["data"]  # type: ignore[return-value]
    if isinstance(payload, MutableMapping):
        return payload  # type: ignore[return-value]
    raise ChartPayloadError("Chart payloads must contain a dict of Highcharts options.")


def ensure_metadata(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    meta = payload.setdefault("meta", {})
    if not isinstance(meta, MutableMapping):
        meta = {"note": str(meta)}
        payload["meta"] = meta
    meta.setdefault("history", [])
    return meta


def append_history_entry(
    payload: MutableMapping[str, Any],
    *,
    actor: str,
    action: str,
    details: Mapping[str, Any] | None = None,
) -> None:
    meta = ensure_metadata(payload)
    history = meta.setdefault("history", [])
    if not isinstance(history, list):
        history = []
        meta["history"] = history

    entry = {
        "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
        "actor": actor,
        "action": action,
    }
    if details:
        entry["details"] = details

    history.append(entry)


def summarize_options(options: Mapping[str, Any]) -> Dict[str, Any]:
    chart_type = options.get("chart", {}).get("type") if isinstance(options.get("chart"), Mapping) else None
    series = options.get("series", []) if isinstance(options.get("series"), Sequence) else []
    summary = {
        "chart_type": chart_type or "unknown",
        "series_count": len(series),
        "series": [],
    }
    for idx, serie in enumerate(series):
        if not isinstance(serie, Mapping):
            continue
        summary["series"].append(
            {
                "index": idx,
                "name": serie.get("name", f"Series {idx + 1}"),
                "type": serie.get("type", chart_type),
                "color": serie.get("color"),
                "dashStyle": serie.get("dashStyle"),
                "dataLabels": bool(serie.get("dataLabels")),
            }
        )
    return summary


def pretty_json(payload: Any) -> str:
    try:
        return json.dumps(payload, indent=2, sort_keys=True)
    except TypeError:
        return str(payload)


# --- Editable field metadata -------------------------------------------------

GLOBAL_FIELD_TEMPLATES: List[Tuple[str, str]] = [
    ("title.text", "Chart title text"),
    ("title.style.color", "Title font color"),
    ("subtitle.text", "Subtitle text"),
    ("subtitle.style.color", "Subtitle font color"),
    ("chart.backgroundColor", "Chart background color"),
    ("xAxis.title.text", "X-axis title"),
    ("xAxis.labels.style", "X-axis label styles"),
    ("yAxis.title.text", "Y-axis title"),
    ("yAxis.labels.style", "Y-axis label styles"),
    ("legend", "Legend configuration"),
    ("legend.enabled", "Toggle legend visibility"),
    ("plotOptions.series.dataLabels", "Global data label options"),
    ("plotOptions.series.dataLabels.enabled", "Enable global data labels"),
    ("plotOptions.series.dataLabels.style", "Global data label style"),
    ("plotOptions.series.marker.enabled", "Global marker visibility"),
]

SERIES_FIELD_TEMPLATES: List[Tuple[str, str]] = [
    ("series[{index}].name", "Series display name"),
    ("series[{index}].color", "Series color"),
    ("series[{index}].dashStyle", "Series line/dash style"),
    ("series[{index}].lineWidth", "Series line width"),
    ("series[{index}].dataLabels.enabled", "Enable series data labels"),
    ("series[{index}].dataLabels.format", "Series data label format"),
    ("series[{index}].dataLabels.style", "Series data label style"),
    ("series[{index}].marker.enabled", "Series marker visibility"),
    ("series[{index}].marker.symbol", "Series marker symbol"),
    ("series[{index}].marker.radius", "Series marker radius"),
]

CHART_TYPE_FIELD_TEMPLATES: Dict[str, List[Tuple[str, str]]] = {
    "column": [
        ("plotOptions.column.colorByPoint", "Color each column by point"),
        ("plotOptions.column.dataLabels.enabled", "Enable column data labels"),
        ("plotOptions.column.dataLabels.style.fontSize", "Column data label font size"),
        ("plotOptions.column.borderRadius", "Column border radius"),
    ],
    "bar": [
        ("plotOptions.bar.dataLabels.enabled", "Enable bar data labels"),
        ("plotOptions.bar.dataLabels.style.fontSize", "Bar data label font size"),
        ("plotOptions.bar.borderRadius", "Bar border radius"),
    ],
    "area": [
        ("plotOptions.area.fillOpacity", "Area fill opacity"),
        ("plotOptions.area.marker.enabled", "Area marker visibility"),
    ],
    "areaspline": [
        ("plotOptions.areaspline.fillOpacity", "Areaspline fill opacity"),
        ("plotOptions.areaspline.marker.enabled", "Areaspline marker visibility"),
    ],
    "line": [
        ("plotOptions.line.marker.enabled", "Line marker visibility"),
    ],
    "spline": [
        ("plotOptions.spline.marker.enabled", "Spline marker visibility"),
    ],
    "pie": [
        ("plotOptions.pie.dataLabels.enabled", "Pie data label toggle"),
        ("plotOptions.pie.dataLabels.distance", "Pie data label distance"),
        ("plotOptions.pie.innerSize", "Pie inner size (donut)"),
        ("plotOptions.pie.showInLegend", "Show pie slices in legend"),
    ],
    "scatter": [
        ("plotOptions.scatter.marker.symbol", "Scatter marker symbol"),
        ("plotOptions.scatter.marker.radius", "Scatter marker radius"),
        ("plotOptions.scatter.marker.fillColor", "Scatter marker fill color"),
    ],
    "bubble": [
        ("plotOptions.bubble.minSize", "Bubble min size"),
        ("plotOptions.bubble.maxSize", "Bubble max size"),
    ],
}


def _allowed_path_patterns_for_chart(chart_type: str | None) -> Set[str]:
    patterns = {template.replace("[{index}]", "[]") for template, _ in GLOBAL_FIELD_TEMPLATES}
    series_patterns = {template.replace("[{index}]", "[]") for template, _ in SERIES_FIELD_TEMPLATES}
    patterns.update(series_patterns)
    if chart_type and chart_type in CHART_TYPE_FIELD_TEMPLATES:
        patterns.update({template.replace("[{index}]", "[]") for template, _ in CHART_TYPE_FIELD_TEMPLATES[chart_type]})
    return patterns


def tokenize_path(path: str) -> List[str | int]:
    if not path:
        raise ChartPayloadError("Update paths cannot be empty.")

    tokens: List[str | int] = []
    buffer = ""
    i = 0
    while i < len(path):
        char = path[i]
        if char == ".":
            if buffer:
                tokens.append(buffer)
                buffer = ""
            i += 1
            continue
        if char == "[":
            if buffer:
                tokens.append(buffer)
                buffer = ""
            end = path.find("]", i)
            if end == -1:
                raise ChartPayloadError(f"Unmatched '[' in path {path}.")
            index_str = path[i + 1 : end]
            if not index_str.isdigit():
                raise ChartPayloadError(f"List index must be numeric in path {path}.")
            tokens.append(int(index_str))
            i = end + 1
            continue
        buffer += char
        i += 1
    if buffer:
        tokens.append(buffer)
    return tokens


def _normalize_tokens(tokens: Sequence[str | int]) -> str:
    normalized: List[str] = []
    for token in tokens:
        if isinstance(token, int):
            if normalized:
                normalized[-1] = normalized[-1] + "[]"
            else:
                normalized.append("[]")
        else:
            normalized.append(token)
    return ".".join(normalized)


def validate_update_path(tokens: Sequence[str | int], chart_type: str | None) -> None:
    pattern = _normalize_tokens(tokens)
    allowed = _allowed_path_patterns_for_chart(chart_type)
    if pattern not in allowed:
        raise ChartPayloadError(f"Path '{pattern}' is not editable for chart type '{chart_type or 'generic'}'.")


def get_nested_value(container: Any, tokens: Sequence[str | int]) -> Any:
    current = container
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, Sequence) or token >= len(current):
                return None
            current = current[token]
        else:
            if not isinstance(current, Mapping) or token not in current:
                return None
            current = current[token]
    return current


def _ensure_sequence(container: MutableSequence[Any], index: int, next_token: str | int) -> MutableMapping[str, Any] | MutableSequence[Any]:
    while len(container) <= index:
        container.append({} if isinstance(next_token, str) else [])
    current = container[index]
    if isinstance(next_token, str) and not isinstance(current, MutableMapping):
        current = {}
        container[index] = current
    if isinstance(next_token, int) and not isinstance(current, MutableSequence):
        current = []
        container[index] = current
    return container[index]


def set_nested_value(container: Any, tokens: Sequence[str | int], value: Any) -> Any:
    current = container
    for idx, token in enumerate(tokens):
        is_last = idx == len(tokens) - 1
        if isinstance(token, int):
            if not isinstance(current, MutableSequence):
                raise ChartPayloadError(f"Expected list while updating path segment {token}.")
            if is_last:
                while len(current) <= token:
                    current.append(None)
                previous = current[token]
                current[token] = value
                return previous
            next_token = tokens[idx + 1]
            target = _ensure_sequence(current, token, next_token)
            current = target
        else:
            if not isinstance(current, MutableMapping):
                raise ChartPayloadError(f"Expected mapping while updating path segment '{token}'.")
            if is_last:
                previous = current.get(token)
                current[token] = value
                return previous
            if token not in current or not isinstance(current[token], (MutableMapping, MutableSequence)):
                current[token] = {} if isinstance(tokens[idx + 1], str) else []
            current = current[token]
    return None


def build_editable_fields(options: Mapping[str, Any]) -> List[Dict[str, Any]]:
    fields: List[Dict[str, Any]] = []
    chart_type = options.get("chart", {}).get("type") if isinstance(options.get("chart"), Mapping) else None

    for template, description in GLOBAL_FIELD_TEMPLATES:
        fields.append({"path": template, "description": description})

    if chart_type and chart_type in CHART_TYPE_FIELD_TEMPLATES:
        for template, description in CHART_TYPE_FIELD_TEMPLATES[chart_type]:
            fields.append({"path": template, "description": description})

    series = options.get("series", []) if isinstance(options.get("series"), Sequence) else []
    for idx, serie in enumerate(series):
        if not isinstance(serie, Mapping):
            continue
        for template, description in SERIES_FIELD_TEMPLATES:
            fields.append({"path": template.format(index=idx), "description": description})

    return fields
