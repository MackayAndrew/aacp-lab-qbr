"""
connectors/mock/notion_mock.py
Realistic Notion API mock for QBR lab v4.
Returns data in Notion API page/block shape.
No API key needed.
"""

import json
from pathlib import Path

DATA = Path(__file__).parent.parent.parent / "data" / "mock"


class MockNotionClient:
    """
    Mimics the Notion API response shape.
    Real NotionClient (v5) uses the same interface.
    """

    def __init__(self, database_id="mock-qbr-notes", period="2026-Q1"):
        self.database_id = database_id
        self.period      = period
        self._data       = json.load(open(DATA / "notion_q1_2026.json"))

    def get_meeting_notes(self, period=None):
        """Returns meeting notes and action items for the period."""
        return {
            "source":   "notion",
            "database": self.database_id,
            "period":   period or self.period,
            "meetings": self._data["meetings"],
        }

    def get_action_items(self, period=None, status=None):
        """Returns action items, optionally filtered by status."""
        items = []
        for meeting in self._data["meetings"]:
            for item in meeting.get("action_items", []):
                if status is None or item["status"] == status:
                    items.append({**item, "meeting_date": meeting["date"]})
        return {
            "source":  "notion",
            "period":  period or self.period,
            "status":  status,
            "items":   items,
            "count":   len(items),
        }
