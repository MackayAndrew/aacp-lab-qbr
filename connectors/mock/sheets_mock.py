"""
connectors/mock/sheets_mock.py
Realistic Google Sheets API mock for QBR lab v4.
Returns data in Sheets API v4 shape.
No API key needed.
"""

import json
from pathlib import Path

DATA = Path(__file__).parent.parent.parent / "data" / "mock"


class MockSheetsClient:
    """
    Mimics the Google Sheets API response shape.
    Real SheetsClient (v5) uses the same interface.
    """

    def __init__(self, spreadsheet_id="mock-budget-2026", period="2026-Q1"):
        self.spreadsheet_id = spreadsheet_id
        self.period         = period
        self._data          = json.load(open(DATA / "sheets_q1_2026.json"))

    def get_budget_actuals(self, period=None, regions=None):
        """Returns budget vs actuals for all regions."""
        data = self._data
        result_regions = data["regions"]
        if regions:
            result_regions = [r for r in result_regions
                             if r["region"] in [x.upper() for x in regions]]
        return {
            "source":      "sheets",
            "spreadsheet": self.spreadsheet_id,
            "period":      period or self.period,
            "regions":     result_regions,
            "flags":       data["flags"],
        }

    def get_variance_summary(self, period=None):
        """Returns departments with material budget variances."""
        material = []
        for region in self._data["regions"]:
            for dept in region["departments"]:
                if abs(dept["variance_pct"]) > 5.0:
                    material.append({
                        "region":   region["region"],
                        "dept":     dept["dept"],
                        "variance_pct": dept["variance_pct"],
                        "variance": dept["variance"],
                        "currency": region["currency"],
                    })
        return {
            "source":            "sheets",
            "period":            period or self.period,
            "material_variances": material,
            "count":             len(material),
        }
