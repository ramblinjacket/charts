from __future__ import annotations

import os

from answer_rocket.client import AnswerRocketClient

from chart_payloads import append_history_entry, ensure_metadata, persist_chart_payload
from skill_runtime import SkillInput, SkillOutput, skill

# Basic Highcharts JSON payload we want to persist with the chat entry
HIGHCHART_CONFIGURATION = {
    "chart": {
      "type": "area"
    },
    "title": {
      "text": "Sample Highchart",
      "style": {
        "fontSize": "20px"
      }
    },
    "xAxis": {
      "categories": [
        "Category A",
        "Category B",
        "Category C"
      ],
      "title": {
        "text": "Categories"
      }
    },
    "yAxis": {
      "title": {
        "text": "Values"
      }
    },
    "series": [
      {
        "name": "Series 1",
        "data": [
          10,
          20,
          30
        ]
      }
    ],
    "credits": {
    },
    "legend": {
      "align": "center",
      "verticalAlign": "bottom",
      "layout": "horizontal"
    },
    "plotOptions": {
      "column": {
        "dataLabels": {
          "style": {
            "fontSize": ""
          }
        }
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
    ensure_metadata(payload)
    append_history_entry(
        payload,
        actor="Data Explorer",
        action="initial_save",
        details={"chart_type": payload.get("data", {}).get("chart", {}).get("type")},
    )

    try:
        saved_id = persist_chart_payload(payload, chat_entry_id=chat_entry_id, client=client)
    except Exception as exc:
        return SkillOutput(final_prompt=f"Chart could not be saved to skill memory ({exc}).")

    return SkillOutput(final_prompt=f"Chart saved to address {saved_id}")
