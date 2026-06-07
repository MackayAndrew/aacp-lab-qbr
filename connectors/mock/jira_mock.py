"""
connectors/mock/jira_mock.py
Realistic Jira API mock for QBR lab v4.
Returns data in Jira REST API shape.
No API key needed.
"""

import json
from pathlib import Path

DATA = Path(__file__).parent.parent.parent / "data" / "mock"


class MockJiraClient:
    """
    Mimics the Jira REST API response shape.
    Real JiraClient (v5) uses the same interface.
    """

    def __init__(self, project_key="PROD", period="2026-Q1"):
        self.project_key = project_key
        self.period      = period
        self._data       = json.load(open(DATA / "jira_q1_2026.json"))

    def get_sprint_metrics(self, period=None):
        """Returns sprint velocity, completion rate, bug metrics."""
        return {
            "source":     "jira",
            "project":    self.project_key,
            "period":     period or self.period,
            "sprints":    self._data["sprints"],
            "okrs":       self._data["okrs"],
            "bugs":       self._data["bugs"],
            "cycle_time": self._data["cycle_time_days"],
        }

    def get_okr_status(self, period=None):
        """Returns OKR progress for the period."""
        return {
            "source":  "jira",
            "period":  period or self.period,
            "okrs":    self._data["okrs"],
        }
