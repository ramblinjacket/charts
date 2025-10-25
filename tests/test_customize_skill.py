from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest import mock

from customize_chart import customize_chart


class DummyInput:
    def __init__(self, **kwargs):
        self.arguments = SimpleNamespace(**kwargs)


class CustomizeChartSkillTest(unittest.TestCase):
    def test_customize_chart_uses_instructions_translator(self) -> None:
        payload = {
            "type": "highcharts",
            "data": {
                "chart": {"type": "line"},
                "series": [
                    {"name": "Series 1", "data": [1, 2, 3]},
                ],
            },
        }

        stored_payload = copy.deepcopy(payload)
        def fake_load(_: str) -> dict:
            return stored_payload

        def fake_extract(source: dict) -> dict:
            return source["data"]

        def fake_persist(updated_payload: dict, **_) -> str:
            self.assertEqual(updated_payload["data"]["series"][0]["color"], "#FF0000")
            self.assertEqual(updated_payload["data"]["series"][0]["dashStyle"], "Dash")
            return "saved-123"

        args = DummyInput(
            saved_payload_id="saved-123",
            updates=None,
            instructions="Make series 1 red dashed lines and enable data labels",
        )

        with mock.patch("customize_chart.load_chart_payload", side_effect=fake_load), \
            mock.patch("customize_chart.extract_chart_options", side_effect=fake_extract), \
            mock.patch("customize_chart.persist_chart_payload", side_effect=fake_persist):
            output = customize_chart(args)

        self.assertIn("#FF0000", output.final_prompt)
        self.assertIn("series[0].dataLabels.enabled", output.final_prompt)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
