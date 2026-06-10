"""
connectors/live/sheets_live.py
Real Google Sheets API connector for QBR Lab v5.
Mirrors MockSheetsClient interface exactly.

Setup:
    .env file with:
    GOOGLE_CREDENTIALS_JSON=/home/ubuntu/aacp-lab-qbr/google_credentials.json
    SHEETS_SPREADSHEET_ID=your-spreadsheet-id
"""

import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/ubuntu/aacp-lab-qbr/.env")


class LiveSheetsClient:
    """
    Real Google Sheets API client.
    Same interface as MockSheetsClient -- agents do not change.
    """

    REGIONS = {
        "EMEA":  {"tab": "EMEA",  "currency": "GBP", "col": "approved_annual_gbp"},
        "NAMER": {"tab": "NAMER", "currency": "USD", "col": "approved_annual_usd"},
    }

    def __init__(self, spreadsheet_id=None, period="2026-Q1"):
        self.spreadsheet_id = (spreadsheet_id or
                               os.environ["SHEETS_SPREADSHEET_ID"])
        self.period         = period
        self._service       = None

    def _get_service(self):
        if self._service is None:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            creds = service_account.Credentials.from_service_account_file(
                os.environ["GOOGLE_CREDENTIALS_JSON"],
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def _read_tab(self, tab_name):
        """Read all rows from a tab. Returns list of dicts."""
        service = self._get_service()
        try:
            result = (service.spreadsheets().values()
                     .get(spreadsheetId=self.spreadsheet_id,
                          range=f"{tab_name}!A:Z")
                     .execute())
            rows = result.get("values", [])
            if not rows:
                return []
            headers = [h.lower().strip() for h in rows[0]]
            return [dict(zip(headers, row)) for row in rows[1:] if row]
        except Exception as e:
            print(f"  Sheets error reading {tab_name}: {e}")
            return []

    def get_budget_actuals(self, period=None, regions=None):
        """
        Read budget data from all region tabs.
        Returns data in the same shape as MockSheetsClient.
        """
        target_regions = regions or list(self.REGIONS.keys())
        result_regions = []
        all_flags      = []

        for region_name in target_regions:
            region_name = region_name.upper()
            if region_name not in self.REGIONS:
                continue

            config = self.REGIONS[region_name]
            rows   = self._read_tab(config["tab"])

            if not rows:
                continue

            departments = []
            for row in rows:
                try:
                    # Handle both GBP and USD column names
                    approved_key = next(
                        (k for k in row if "approved" in k), None)
                    ytd_key      = next(
                        (k for k in row if "ytd" in k), None)

                    if not approved_key or not ytd_key:
                        continue

                    approved = float(row.get(approved_key, 0) or 0)
                    ytd      = float(row.get(ytd_key, 0) or 0)

                    if approved == 0:
                        continue

                    variance     = round(ytd - approved, 2)
                    variance_pct = round((variance / approved) * 100, 1)
                    flagged      = abs(variance_pct) > 5.0

                    dept = {
                        "cc_id":            row.get("cc_id", ""),
                        "cc_name":          row.get("cc_name", ""),
                        "approved_annual":  approved,
                        "ytd_spend":        ytd,
                        "remaining":        round(approved - ytd, 2),
                        "utilisation_pct":  round((ytd / approved) * 100, 1),
                        "variance":         variance,
                        "variance_pct":     variance_pct,
                        "currency":         config["currency"],
                        "owner":            row.get("owner", ""),
                        "flagged":          flagged,
                    }
                    departments.append(dept)

                    if flagged:
                        direction = "Over" if variance_pct > 0 else "Under"
                        all_flags.append({
                            "region":   region_name,
                            "dept":     row.get("cc_name", ""),
                            "flag":     (f"{direction} budget by "
                                        f"{abs(variance_pct):.1f}%"),
                            "variance_pct": variance_pct,
                        })

                except (ValueError, TypeError) as e:
                    continue

            result_regions.append({
                "region":      region_name,
                "currency":    config["currency"],
                "departments": departments,
            })

        return {
            "source":      "sheets_live",
            "spreadsheet": self.spreadsheet_id,
            "period":      period or self.period,
            "regions":     result_regions,
            "flags":       all_flags,
        }

    def get_variance_summary(self, period=None):
        """Returns departments with material budget variances (>5%)."""
        data     = self.get_budget_actuals(period)
        material = []
        for region in data["regions"]:
            for dept in region["departments"]:
                if abs(dept["variance_pct"]) > 5.0:
                    material.append({
                        "region":       region["region"],
                        "dept":         dept["cc_name"],
                        "variance_pct": dept["variance_pct"],
                        "variance":     dept["variance"],
                        "currency":     dept["currency"],
                    })
        return {
            "source":             "sheets_live",
            "period":             period or self.period,
            "material_variances": material,
            "count":              len(material),
        }


if __name__ == "__main__":
    client = LiveSheetsClient()
    data   = client.get_budget_actuals()
    print(json.dumps(data, indent=2))
