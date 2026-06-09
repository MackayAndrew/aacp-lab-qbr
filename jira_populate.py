"""
Jira population script for AACP QBR Lab v5.
Creates sprints, issues and OKR epics matching mock data shapes.

Run:
    python3 jira_populate.py
"""

import os
import json
import base64
import urllib.request
import urllib.error
import time
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/ubuntu/aacp-lab-qbr/.env")

BASE_URL    = os.environ["JIRA_BASE_URL"]
EMAIL       = os.environ["JIRA_EMAIL"]
TOKEN       = os.environ["JIRA_API_TOKEN"]
PROJECT_KEY = os.environ.get("JIRA_PROJECT", "AL")

CREDS = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {CREDS}",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
}


def api(method, path, data=None):
    url = f"{BASE_URL}/rest/api/3/{path.lstrip('/')}"
    body = json.dumps(data).encode() if data else None
    req  = urllib.request.Request(url, data=body,
                                  headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()) if resp.read() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERROR {e.code}: {body[:200]}")
        return None


def agile_api(method, path, data=None):
    url  = f"{BASE_URL}/rest/agile/1.0/{path.lstrip('/')}"
    body = json.dumps(data).encode() if data else None
    req  = urllib.request.Request(url, data=body,
                                  headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req)
        raw  = resp.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ERROR {e.code}: {body[:200]}")
        return None


# ── Step 1: Get project info ──────────────────────────────────────────────

print("\n1. Checking project...")
project = api("GET", f"project/{PROJECT_KEY}")
if not project:
    print(f"   ERROR: Project {PROJECT_KEY} not found")
    exit(1)
print(f"   Project: {project['name']} ({PROJECT_KEY})")
project_id = project["id"]


# ── Step 2: Get or create board ───────────────────────────────────────────

print("\n2. Getting board...")
boards = agile_api("GET", f"board?projectKeyOrId={PROJECT_KEY}")
if boards and boards.get("values"):
    board_id = boards["values"][0]["id"]
    print(f"   Board ID: {board_id}")
else:
    print("   No board found -- creating one")
    board = agile_api("POST", "board", {
        "name": f"{PROJECT_KEY} Board",
        "type": "scrum",
        "filterId": None,
        "location": {"projectKeyOrId": PROJECT_KEY}
    })
    if not board:
        print("   Could not create board -- continuing without sprints")
        board_id = None
    else:
        board_id = board["id"]
        print(f"   Board created: {board_id}")


# ── Step 3: Create OKR epics ──────────────────────────────────────────────

print("\n3. Creating OKR epics...")
epics = [
    {
        "summary": "OKR: Reduce customer onboarding time by 40%",
        "description": "Target: reduce time-to-first-value from 14 days to 8 days by end of Q1 2026.",
    },
    {
        "summary": "OKR: Ship product integrations to unlock enterprise deals",
        "description": "Deliver Salesforce integration, Jira integration, and SSO/SAML support.",
    },
]

epic_ids = []
for epic in epics:
    result = api("POST", "issue", {
        "fields": {
            "project":     {"key": PROJECT_KEY},
            "summary":     epic["summary"],
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": epic["description"]}
                ]}]
            },
            "issuetype": {"name": "Epic"},
        }
    })
    if result:
        epic_ids.append(result["key"])
        print(f"   Created epic: {result['key']} -- {epic['summary'][:50]}")
    time.sleep(0.3)


# ── Step 4: Create key results as stories ─────────────────────────────────

print("\n4. Creating key result stories...")
key_results = [
    {"summary": "KR: Reduce time-to-first-value from 14 days to 8 days",
     "story_points": 13, "status": "In Progress"},
    {"summary": "KR: Automate 3 manual onboarding steps",
     "story_points": 8,  "status": "Done"},
    {"summary": "KR: NPS score for new customers above 50",
     "story_points": 5,  "status": "Done"},
    {"summary": "KR: Deliver Salesforce integration",
     "story_points": 21, "status": "Done"},
    {"summary": "KR: Deliver Jira integration",
     "story_points": 13, "status": "Done"},
    {"summary": "KR: Deliver SSO / SAML support",
     "story_points": 21, "status": "To Do"},
]

for kr in key_results:
    result = api("POST", "issue", {
        "fields": {
            "project":   {"key": PROJECT_KEY},
            "summary":   kr["summary"],
            "issuetype": {"name": "Story"},
        }
    })
    if result:
        print(f"   Created: {result['key']} -- {kr['summary'][:55]}")
    time.sleep(0.3)


# ── Step 5: Create sprint tasks ───────────────────────────────────────────

print("\n5. Creating sprint tasks...")
tasks = [
    # Onboarding improvement
    {"summary": "Investigate onboarding funnel drop-off points", "points": 5},
    {"summary": "Automate welcome email sequence", "points": 3},
    {"summary": "Build self-serve setup wizard v1", "points": 8},
    {"summary": "Customer interview -- onboarding feedback x5", "points": 5},
    # Integrations
    {"summary": "Salesforce connector -- OAuth flow", "points": 8},
    {"summary": "Salesforce connector -- bi-directional sync", "points": 13},
    {"summary": "SSO SAML implementation -- research spike", "points": 5},
    {"summary": "SSO security review -- vendor assessment", "points": 3},
    # Bugs
    {"summary": "[BUG] Critical: payment module double-charge on retry", "points": 8},
    {"summary": "[BUG] Critical: onboarding step 3 fails for EU accounts", "points": 5},
    {"summary": "[BUG] P1: dashboard load timeout >30s for large accounts", "points": 3},
    # Platform
    {"summary": "Migrate auth service to Entra ID", "points": 13},
    {"summary": "Performance: reduce API p90 latency by 30%", "points": 8},
    {"summary": "Add structured logging to all services", "points": 5},
    {"summary": "Q1 retrospective action items", "points": 3},
]

created_keys = []
for task in tasks:
    result = api("POST", "issue", {
        "fields": {
            "project":   {"key": PROJECT_KEY},
            "summary":   task["summary"],
            "issuetype": {"name": "Task"},
        }
    })
    if result:
        created_keys.append(result["key"])
        print(f"   Created: {result['key']} -- {task['summary'][:55]}")
    time.sleep(0.3)


# ── Step 6: Create sprints if board available ─────────────────────────────

if board_id:
    print("\n6. Creating sprints...")
    sprints_data = [
        {"name": "Sprint 10", "start": "2026-01-05", "end": "2026-01-16"},
        {"name": "Sprint 11", "start": "2026-01-19", "end": "2026-01-30"},
        {"name": "Sprint 12", "start": "2026-02-02", "end": "2026-02-13"},
        {"name": "Sprint 13", "start": "2026-02-16", "end": "2026-02-27"},
        {"name": "Sprint 14", "start": "2026-03-02", "end": "2026-03-13"},
        {"name": "Sprint 15", "start": "2026-03-16", "end": "2026-03-27"},
    ]

    sprint_ids = []
    for sp in sprints_data:
        result = agile_api("POST", "sprint", {
            "name":          sp["name"],
            "startDate":     f"{sp['start']}T09:00:00.000Z",
            "endDate":       f"{sp['end']}T17:00:00.000Z",
            "originBoardId": board_id,
        })
        if result and result.get("id"):
            sprint_ids.append(result["id"])
            print(f"   Created: {sp['name']} (id: {result['id']})")
        else:
            print(f"   Could not create sprint {sp['name']} -- skipping")
        time.sleep(0.3)

    # Assign tasks to sprints
    if sprint_ids and created_keys:
        print("\n   Assigning issues to sprints...")
        chunks = [created_keys[i:i+3] for i in range(0, len(created_keys), 3)]
        for i, (sid, chunk) in enumerate(zip(sprint_ids, chunks)):
            agile_api("POST", f"sprint/{sid}/issue", {"issues": chunk})
            print(f"   Sprint {i+10}: assigned {chunk}")
            time.sleep(0.3)
else:
    print("\n6. Skipping sprints -- no board available")


print(f"""
============================================================
  Jira population complete
  Project: {PROJECT_KEY} at {BASE_URL}
  Epics:   {len(epic_ids)}
  Stories: {len(key_results)}
  Tasks:   {len(created_keys)}
============================================================
""")
