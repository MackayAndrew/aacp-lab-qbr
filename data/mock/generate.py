"""
Generate realistic mock data for the QBR lab.
Run once to create all mock data files.
Produces data that looks like real Jira, Notion and Sheets
API responses -- same shape, realistic content.
"""

import json
from pathlib import Path

OUT = Path(__file__).parent


# ── Jira mock data ────────────────────────────────────────────────────────
# Mirrors Jira REST API /rest/agile/1.0/board/{id}/sprint shape

jira_sprints = {
    "sprints": [
        {"id": 101, "name": "Sprint 10", "state": "closed",
         "startDate": "2026-01-05", "endDate": "2026-01-16",
         "completed_points": 42, "committed_points": 48, "velocity": 42},
        {"id": 102, "name": "Sprint 11", "state": "closed",
         "startDate": "2026-01-19", "endDate": "2026-01-30",
         "completed_points": 51, "committed_points": 50, "velocity": 51},
        {"id": 103, "name": "Sprint 12", "state": "closed",
         "startDate": "2026-02-02", "endDate": "2026-02-13",
         "completed_points": 38, "committed_points": 52, "velocity": 38},
        {"id": 104, "name": "Sprint 13", "state": "closed",
         "startDate": "2026-02-16", "endDate": "2026-02-27",
         "completed_points": 55, "committed_points": 54, "velocity": 55},
        {"id": 105, "name": "Sprint 14", "state": "closed",
         "startDate": "2026-03-02", "endDate": "2026-03-13",
         "completed_points": 49, "committed_points": 50, "velocity": 49},
        {"id": 106, "name": "Sprint 15", "state": "closed",
         "startDate": "2026-03-16", "endDate": "2026-03-27",
         "completed_points": 53, "committed_points": 52, "velocity": 53},
    ],
    "okrs": [
        {"objective": "Reduce customer onboarding time by 40%",
         "key_results": [
             {"kr": "Reduce time-to-first-value from 14 days to 8 days",
              "target": 8, "current": 9.5, "unit": "days", "on_track": False},
             {"kr": "Automate 3 manual onboarding steps",
              "target": 3, "current": 3, "unit": "steps", "on_track": True},
             {"kr": "NPS score for new customers above 50",
              "target": 50, "current": 54, "unit": "score", "on_track": True},
         ]},
        {"objective": "Ship product integrations that unlock enterprise deals",
         "key_results": [
             {"kr": "Deliver Salesforce integration",
              "target": 1, "current": 1, "unit": "integrations", "on_track": True},
             {"kr": "Deliver Jira integration",
              "target": 1, "current": 1, "unit": "integrations", "on_track": True},
             {"kr": "Deliver SSO / SAML support",
              "target": 1, "current": 0, "unit": "integrations", "on_track": False},
         ]},
    ],
    "bugs": {
        "opened_q1": 47, "closed_q1": 39, "open_end_q1": 23,
        "critical_open": 2, "p1_sla_breaches": 1,
    },
    "cycle_time_days": {"p50": 3.2, "p90": 8.7},
}

# ── Notion mock data ──────────────────────────────────────────────────────
# Mirrors Notion API /v1/blocks/{page_id}/children shape
# Represents extracted meeting notes from Q1 2026

notion_meeting_notes = {
    "period": "2026-Q1",
    "meetings": [
        {
            "date": "2026-01-08",
            "title": "Q1 Kick-off",
            "attendees": ["Sarah Chen", "Marcus Webb", "David Park", "Linda Torres"],
            "decisions": [
                "SSO delivery pushed to Q2 due to security review dependency",
                "Onboarding time target confirmed at 8 days by end of Q1",
                "Engineering capacity locked -- no new projects until March",
            ],
            "action_items": [
                {"owner": "Marcus Webb", "action": "Confirm enterprise pipeline forecast with sales team", "due": "2026-01-15", "status": "complete"},
                {"owner": "David Park", "action": "Initiate security review for SSO vendor", "due": "2026-01-22", "status": "complete"},
            ],
        },
        {
            "date": "2026-02-05",
            "title": "February Review",
            "attendees": ["Sarah Chen", "Marcus Webb", "David Park"],
            "decisions": [
                "Sprint 12 velocity drop attributed to two engineers on leave",
                "Salesforce integration shipped on schedule",
                "Onboarding time at 11 days -- intervention required",
            ],
            "action_items": [
                {"owner": "Sarah Chen", "action": "Review onboarding funnel and identify top three blockers", "due": "2026-02-12", "status": "complete"},
                {"owner": "Linda Torres", "action": "Schedule customer interviews for onboarding feedback", "due": "2026-02-19", "status": "complete"},
            ],
        },
        {
            "date": "2026-03-05",
            "title": "March Review",
            "attendees": ["Sarah Chen", "Marcus Webb", "David Park", "Linda Torres"],
            "decisions": [
                "Onboarding improvement plan delivered -- time now at 9.5 days",
                "Two critical bugs identified in payment module -- fix prioritised",
                "SSO security review complete -- build begins Q2 Sprint 1",
            ],
            "action_items": [
                {"owner": "David Park", "action": "Patch critical payment bugs before Q1 close", "due": "2026-03-15", "status": "complete"},
                {"owner": "Marcus Webb", "action": "Prepare Q1 pipeline report for board pack", "due": "2026-03-28", "status": "in_progress"},
                {"owner": "Sarah Chen", "action": "Draft Q1 engineering retrospective", "due": "2026-03-28", "status": "in_progress"},
            ],
        },
    ],
}

# ── Google Sheets mock data ───────────────────────────────────────────────
# Mirrors Sheets API v4 spreadsheets.values.get shape
# Two regional budget sheets consolidated

sheets_budget = {
    "period": "2026-Q1",
    "regions": [
        {
            "region": "EMEA",
            "currency": "GBP",
            "departments": [
                {"dept": "Engineering", "approved_q1": 420000, "actual_q1": 398500, "variance": -21500, "variance_pct": -5.1},
                {"dept": "Sales", "approved_q1": 140000, "actual_q1": 152300, "variance": 12300, "variance_pct": 8.8},
                {"dept": "Marketing", "approved_q1": 85000, "actual_q1": 79200, "variance": -5800, "variance_pct": -6.8},
                {"dept": "Operations", "approved_q1": 95000, "actual_q1": 97100, "variance": 2100, "variance_pct": 2.2},
            ],
        },
        {
            "region": "NAMER",
            "currency": "USD",
            "departments": [
                {"dept": "Engineering", "approved_q1": 680000, "actual_q1": 671000, "variance": -9000, "variance_pct": -1.3},
                {"dept": "Sales", "approved_q1": 310000, "actual_q1": 334500, "variance": 24500, "variance_pct": 7.9},
                {"dept": "Marketing", "approved_q1": 120000, "actual_q1": 118400, "variance": -1600, "variance_pct": -1.3},
                {"dept": "Operations", "approved_q1": 75000, "actual_q1": 74200, "variance": -800, "variance_pct": -1.1},
            ],
        },
    ],
    "flags": [
        {"region": "EMEA", "dept": "Sales", "flag": "Over budget by 8.8% -- pipeline growth driving spend"},
        {"region": "NAMER", "dept": "Sales", "flag": "Over budget by 7.9% -- consistent with EMEA, pipeline-driven"},
    ],
}

# ── Write files ────────────────────────────────────────────────────────────
with open(OUT / "jira_q1_2026.json", "w") as f:
    json.dump(jira_sprints, f, indent=2)

with open(OUT / "notion_q1_2026.json", "w") as f:
    json.dump(notion_meeting_notes, f, indent=2)

with open(OUT / "sheets_q1_2026.json", "w") as f:
    json.dump(sheets_budget, f, indent=2)

print("Mock data generated:")
for p in sorted(OUT.glob("*.json")):
    print(f"  {p.name}  ({p.stat().st_size:,} bytes)")
