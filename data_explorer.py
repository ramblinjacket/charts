from __future__ import annotations

import os

from answer_rocket.client import AnswerRocketClient
from skill_framework.skills import SkillInput, SkillOutput, skill

# Basic Highcharts JSON payload we want to persist with the chat entry
HIGHCHART_CONFIGURATION = {
    "chart": {
      "type": "bar"
    },
    "title": {
      "text": "Top 8 Segments by Total Sales (2022)",
      "style": {
        "fontSize": "18px",
        "fontWeight": "bold"
      }
    },
    "series": [
      {
        "name": "total_sales",
        "data": [
          799834847.8699951,
          798769147.5819905,
          568545246.4949996,
          117811767.06799985,
          39237618.809,
          20666835.681,
          1366.1100000000001
        ]
      }
    ],
    "yAxis": {
      "title": {
        "text": ""
      }
    },
    "xAxis": {
      "categories": [
        "sample",
        "chart",
        "FILLED PASTA",
        "BAKING",
        "this",
        "is",
        "a"
      ],
      "title": {
        "text": ""
      }
    }
  }


@skill(
    name="Data Explorer",
    description="Run to retrieve data for a user",
)
def save_chart(_: SkillInput) -> SkillOutput:
    """
    Persist the hard-coded Highcharts configuration with the current chat entry so it can be reused later.
    """
    client = AnswerRocketClient()
    chat_entry_id = client._client_config.chat_entry_id or os.getenv("AR_CHAT_ENTRY_ID")

    if not chat_entry_id:
        return SkillOutput(final_prompt="Chart could not be saved because no chat entry ID was available.")

    payload = {"type": "highcharts", "data": HIGHCHART_CONFIGURATION}
    did_save = client.chat.set_skill_memory_payload(payload, chat_entry_id=chat_entry_id)

    if not did_save:
        return SkillOutput(final_prompt="Chart could not be saved to skill memory.")

    return SkillOutput(final_prompt=f"Chart saved to address {chat_entry_id}")
