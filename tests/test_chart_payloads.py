from __future__ import annotations

import unittest

from chart_payloads import (
    ChartPayloadError,
    build_editable_fields,
    get_nested_value,
    set_nested_value,
    tokenize_path,
    validate_update_path,
)


class ChartPayloadHelpersTest(unittest.TestCase):
    def test_tokenize_path_with_indices(self) -> None:
        tokens = tokenize_path("series[1].dataLabels.enabled")
        self.assertEqual(tokens, ["series", 1, "dataLabels", "enabled"])

    def test_validate_update_path_allows_title(self) -> None:
        tokens = tokenize_path("title.text")
        try:
            validate_update_path(tokens, "area")
        except ChartPayloadError as exc:  # pragma: no cover - should not happen
            self.fail(f"validate_update_path raised unexpectedly: {exc}")

    def test_validate_update_path_blocks_unknown_field(self) -> None:
        tokens = tokenize_path("series[0].unknownField")
        with self.assertRaises(ChartPayloadError):
            validate_update_path(tokens, "area")

    def test_set_nested_value_updates_structure(self) -> None:
        options = {"series": [{"name": "A"}]}
        tokens = tokenize_path("series[0].color")
        validate_update_path(tokens, None)
        set_nested_value(options, tokens, "#ff0000")
        self.assertEqual(get_nested_value(options, tokens), "#ff0000")

    def test_build_editable_fields_includes_series_templates(self) -> None:
        options = {"chart": {"type": "area"}, "series": [{"name": "A"}, {"name": "B"}]}
        editable = build_editable_fields(options)
        paths = {entry["path"] for entry in editable}
        self.assertIn("series[0].color", paths)
        self.assertIn("series[1].dashStyle", paths)
        self.assertIn("plotOptions.area.fillOpacity", paths)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
