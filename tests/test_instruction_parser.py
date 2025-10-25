from __future__ import annotations

import unittest

from chart_instruction_parser import instructions_to_updates


def _updates_map(updates):
    return {update["path"]: update["value"] for update in updates}


class InstructionParserTest(unittest.TestCase):
    def test_color_dash_linewidth_for_series(self) -> None:
        options = {"chart": {"type": "line"}, "series": [{"name": "Alpha"}, {"name": "Beta"}]}
        instructions = "Make series 1 red dashed lines with line width 3px"
        updates = instructions_to_updates(instructions, options)
        mapped = _updates_map(updates)
        self.assertEqual(mapped.get("series[0].color"), "#FF0000")
        self.assertEqual(mapped.get("series[0].dashStyle"), "Dash")
        self.assertEqual(mapped.get("series[0].lineWidth"), 3)

    def test_enable_global_data_labels(self) -> None:
        options = {"chart": {"type": "column"}, "series": [{"name": "Sales"}]}
        instructions = "Please enable data labels for all series"
        updates = instructions_to_updates(instructions, options)
        mapped = _updates_map(updates)
        self.assertTrue(mapped.get("plotOptions.series.dataLabels.enabled"))

    def test_fill_opacity_for_area_chart(self) -> None:
        options = {"chart": {"type": "area"}, "series": [{"name": "Area"}]}
        instructions = "Set the fill opacity to 40%"
        updates = instructions_to_updates(instructions, options)
        mapped = _updates_map(updates)
        self.assertAlmostEqual(mapped.get("plotOptions.area.fillOpacity"), 0.4)

    def test_marker_updates_for_scatter_chart(self) -> None:
        options = {"chart": {"type": "scatter"}, "series": [{"name": "Scatter"}]}
        instructions = "Turn off the markers and set their radius to 6px"
        updates = instructions_to_updates(instructions, options)
        mapped = _updates_map(updates)
        self.assertFalse(mapped.get("plotOptions.scatter.marker.enabled"))
        self.assertEqual(mapped.get("plotOptions.scatter.marker.radius"), 6)

    def test_pie_donut_instruction(self) -> None:
        options = {"chart": {"type": "pie"}, "series": [{"name": "Share"}]}
        instructions = "Make this pie a donut with inner size 70% and hide the legend"
        updates = instructions_to_updates(instructions, options)
        mapped = _updates_map(updates)
        self.assertEqual(mapped.get("plotOptions.pie.innerSize"), "70%")
        self.assertFalse(mapped.get("legend.enabled"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
