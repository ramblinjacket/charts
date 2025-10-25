from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence

COLOR_NAME_MAP = {
    "red": "#FF0000",
    "blue": "#1F77B4",
    "green": "#2CA02C",
    "orange": "#FF7F0E",
    "purple": "#9467BD",
    "yellow": "#F2C200",
    "black": "#000000",
    "white": "#FFFFFF",
    "gray": "#808080",
    "grey": "#808080",
    "pink": "#E377C2",
    "teal": "#17BECF",
}

DASH_KEYWORDS = [
    ("short dash dot", "ShortDashDot"),
    ("short dash", "ShortDash"),
    ("long dash", "LongDash"),
    ("dashdot", "DashDot"),
    ("dash-dot", "DashDot"),
    ("dotted", "Dot"),
    ("dot", "Dot"),
    ("dashed", "Dash"),
    ("dash", "Dash"),
    ("solid", "Solid"),
]

ORDINAL_WORD_MAP = {
    "first": 0,
    "second": 1,
    "third": 2,
    "fourth": 3,
    "fifth": 4,
    "sixth": 5,
    "seventh": 6,
    "eighth": 7,
    "ninth": 8,
    "tenth": 9,
}

POSITIVE_BOOL_PHRASES = (
    "enable",
    "turn on",
    "turn it on",
    "show",
    "display",
    "activate",
    "add",
    "use",
)
NEGATIVE_BOOL_PHRASES = (
    "disable",
    "turn off",
    "turn it off",
    "hide",
    "remove",
    "deactivate",
    "suppress",
)

HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
RGB_COLOR_RE = re.compile(r"rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)", re.IGNORECASE)
SERIES_NUMBER_RE = re.compile(r"series\s+(?P<num>\d+)", re.IGNORECASE)
ORDINAL_SERIES_RE = re.compile(
    r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(series|line|bar|column|area)\b",
    re.IGNORECASE,
)
LINE_WIDTH_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:px|pt)?\s*(?:line width|linewidth|thickness|stroke)", re.IGNORECASE),
    re.compile(r"(?:line width|linewidth|thickness|stroke)\s*(?:of|to)?\s*(\d+(?:\.\d+)?)(?:\s*(?:px|pt))?", re.IGNORECASE),
]
FILL_OPACITY_RE = re.compile(r"fill opacity.*?(\d+(?:\.\d+)?%?)", re.IGNORECASE)
INNER_SIZE_RE = re.compile(r"inner size.*?(\d+%)", re.IGNORECASE)
DONUT_SIZE_RE = re.compile(r"(donut|doughnut).*?(\d+%)", re.IGNORECASE)
RADIUS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:px)?\s*(?:radius|size)", re.IGNORECASE)
RADIUS_AFTER_RE = re.compile(r"(?:radius|size).*?(\d+(?:\.\d+)?)(?:\s*px)?", re.IGNORECASE)

MARKER_SYMBOL_MAP = {
    "circle": "circle",
    "square": "square",
    "diamond": "diamond",
    "triangle": "triangle",
    "triangle-down": "triangle-down",
    "triangle down": "triangle-down",
}

AREA_LIKE_TYPES = {"area", "areaspline"}
MARKER_CHART_TYPES = {"line", "spline", "area", "areaspline", "scatter"}


def instructions_to_updates(instructions: str, options: Mapping[str, Any]) -> List[Dict[str, Any]]:
    if not instructions:
        return []

    chart_config = options.get("chart") if isinstance(options.get("chart"), Mapping) else None
    chart_type = chart_config.get("type") if isinstance(chart_config, Mapping) else None
    series = options.get("series", []) if isinstance(options.get("series"), Sequence) else []

    sentences = [segment.strip() for segment in re.split(r"[.;\n]+", instructions) if segment.strip()]
    updates: List[Dict[str, Any]] = []

    for sentence in sentences:
        lowered = sentence.lower()
        targets = _series_targets(lowered, series)

        color_value = _extract_color(sentence, lowered)
        if color_value and targets:
            for idx in targets:
                updates.append({"path": f"series[{idx}].color", "value": color_value})

        dash_value = _extract_dash_style(lowered)
        if dash_value and targets:
            for idx in targets:
                updates.append({"path": f"series[{idx}].dashStyle", "value": dash_value})

        line_width_value = _extract_line_width(sentence)
        if line_width_value is not None and targets:
            for idx in targets:
                updates.append({"path": f"series[{idx}].lineWidth", "value": line_width_value})

        if "data label" in lowered:
            bool_value = _detect_boolean(lowered)
            if bool_value is not None:
                if targets and not _mentions_all_series(lowered):
                    for idx in targets:
                        updates.append({"path": f"series[{idx}].dataLabels.enabled", "value": bool_value})
                else:
                    updates.append({"path": "plotOptions.series.dataLabels.enabled", "value": bool_value})

        if "legend" in lowered:
            bool_value = _detect_boolean(lowered)
            if bool_value is not None:
                updates.append({"path": "legend.enabled", "value": bool_value})

        if "marker" in lowered:
            bool_value = _detect_boolean(lowered)
            if bool_value is not None:
                marker_path = _marker_enabled_path(chart_type)
                if marker_path:
                    updates.append({"path": marker_path, "value": bool_value})
                elif targets:
                    for idx in targets:
                        updates.append({"path": f"series[{idx}].marker.enabled", "value": bool_value})

            marker_radius = _extract_marker_radius(sentence)
            if marker_radius is not None:
                if chart_type == "scatter":
                    updates.append({"path": "plotOptions.scatter.marker.radius", "value": marker_radius})
                elif targets:
                    for idx in targets:
                        updates.append({"path": f"series[{idx}].marker.radius", "value": marker_radius})

            marker_symbol = _extract_marker_symbol(lowered)
            if marker_symbol:
                if chart_type == "scatter":
                    updates.append({"path": "plotOptions.scatter.marker.symbol", "value": marker_symbol})
                elif targets:
                    for idx in targets:
                        updates.append({"path": f"series[{idx}].marker.symbol", "value": marker_symbol})

        if color_value and not targets and chart_type == "scatter" and "marker" in lowered:
            updates.append({"path": "plotOptions.scatter.marker.fillColor", "value": color_value})

        if chart_type in AREA_LIKE_TYPES:
            opacity_value = _extract_fill_opacity(sentence)
            if opacity_value is not None:
                updates.append({"path": f"plotOptions.{chart_type}.fillOpacity", "value": opacity_value})

        if chart_type == "pie":
            donut_value = _extract_inner_size(sentence)
            if donut_value:
                updates.append({"path": "plotOptions.pie.innerSize", "value": donut_value})
            if "legend" in lowered:
                bool_value = _detect_boolean(lowered)
                if bool_value is not None:
                    updates.append({"path": "plotOptions.pie.showInLegend", "value": bool_value})
            if "data label" in lowered:
                bool_value = _detect_boolean(lowered)
                if bool_value is not None:
                    updates.append({"path": "plotOptions.pie.dataLabels.enabled", "value": bool_value})

    return updates


def _series_targets(sentence: str, series: Sequence[Any]) -> List[int]:
    if not isinstance(series, Sequence):
        return []

    total = len(series)
    if total == 0:
        return []

    if "all series" in sentence or "every series" in sentence:
        return list(range(total))

    match = SERIES_NUMBER_RE.search(sentence)
    if match:
        idx = int(match.group("num")) - 1
        if 0 <= idx < total:
            return [idx]

    match = ORDINAL_SERIES_RE.search(sentence)
    if match:
        word = match.group(1).lower()
        idx = ORDINAL_WORD_MAP.get(word)
        if idx is not None and idx < total:
            return [idx]

    for idx, serie in enumerate(series):
        name = str(serie.get("name", "")) if isinstance(serie, Mapping) else ""
        if name and name.lower() in sentence:
            return [idx]

    if "series" in sentence and total == 1:
        return [0]

    return []


def _extract_color(sentence: str, lowered: str) -> str | None:
    hex_match = HEX_COLOR_RE.search(sentence)
    if hex_match:
        return hex_match.group(0).upper()

    rgb_match = RGB_COLOR_RE.search(sentence)
    if rgb_match:
        return rgb_match.group(0)

    for name, hex_value in COLOR_NAME_MAP.items():
        if re.search(rf"\b{name}\b", lowered):
            return hex_value

    return None


def _extract_dash_style(lowered: str) -> str | None:
    for keyword, dash in DASH_KEYWORDS:
        if keyword in lowered:
            return dash
    return None


def _extract_line_width(sentence: str) -> float | int | None:
    for pattern in LINE_WIDTH_PATTERNS:
        match = pattern.search(sentence)
        if match:
            value = float(match.group(1))
            if value.is_integer():
                return int(value)
            return value
    return None


def _detect_boolean(lowered: str) -> bool | None:
    for phrase in NEGATIVE_BOOL_PHRASES:
        if phrase in lowered:
            return False
    for phrase in POSITIVE_BOOL_PHRASES:
        if phrase in lowered:
            return True
    return None


def _extract_fill_opacity(sentence: str) -> float | None:
    match = FILL_OPACITY_RE.search(sentence)
    if not match:
        return None
    value = match.group(1).strip()
    if value.endswith("%"):
        numeric = float(value[:-1]) / 100
    else:
        numeric = float(value)
    return max(0.0, min(1.0, numeric))


def _extract_inner_size(sentence: str) -> str | None:
    match = INNER_SIZE_RE.search(sentence)
    if match:
        return match.group(1)
    match = DONUT_SIZE_RE.search(sentence)
    if match:
        return match.group(2)
    if "donut" in sentence.lower() or "doughnut" in sentence.lower():
        return "60%"
    return None


def _marker_enabled_path(chart_type: str | None) -> str | None:
    if not chart_type:
        return "plotOptions.series.marker.enabled"
    if chart_type in {"line", "area", "spline", "areaspline"}:
        return f"plotOptions.{chart_type}.marker.enabled"
    if chart_type == "scatter":
        return "plotOptions.scatter.marker.enabled"
    return "plotOptions.series.marker.enabled"


def _extract_marker_radius(sentence: str) -> float | int | None:
    match = RADIUS_RE.search(sentence)
    if not match:
        match = RADIUS_AFTER_RE.search(sentence)
    if not match:
        return None
    value = float(match.group(1))
    if value.is_integer():
        return int(value)
    return value


def _extract_marker_symbol(lowered: str) -> str | None:
    for keyword, symbol in MARKER_SYMBOL_MAP.items():
        if keyword in lowered:
            return symbol
    return None


def _mentions_all_series(sentence: str) -> bool:
    return "all series" in sentence or "every series" in sentence


__all__ = ["instructions_to_updates"]
