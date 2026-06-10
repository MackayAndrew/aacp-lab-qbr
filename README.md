# AACP QBR Lab

**Quarterly Business Review workflow using AACP coordination.**

Five agents. Six coordination hops. Real business data.
AACP packets coordinate the agents throughout. Zero coordination LLM cost.

Two run modes:
- `--mock` -- no service API keys needed, anyone can run it
- `--live` -- real Jira, Notion and Google Sheets connections

---

## What this demonstrates

A QBR workflow that reflects how a real business review is assembled:

1. **MetricsAgent** fetches sprint velocity and OKR progress from Jira
2. **NotesAgent** extracts decisions and action items from Notion meeting notes
3. **BudgetAgent** retrieves actuals vs budget from Google Sheets
4. **ConsolidateAgent** merges all three sources into a single coherent view
5. **NarrativeAgent** drafts the executive summary for human review
6. **AuditAgent** writes a structured audit record at zero LLM cost

All six coordination hops use AACP packets. The agents receive typed,
validated instructions -- not natural language that varies on every run.

---

## The cadence hierarchy

The same workflow and the same encoder work at every review cadence.

| Cadence | Period format | Narrative depth |
|---|---|---|
| Daily | 2026-06-07 | Anomalies and blockers only |
| Weekly | 2026-W23 | Progress, risks, blockers |
| Monthly | 2026-03 | Summary, highlights, budget flag |
| Quarterly | 2026-Q1 | Full narrative with recommendation |

---

## Quick start (mock -- no service API keys needed)

```bash
pip install aacp langchain-openai
export OPENAI_API_KEY=sk-...
python3 run_qbr.py --mock
python3 run_qbr.py --mock --cadence monthly  --period 2026-03
python3 run_qbr.py --mock --cadence weekly   --period 2026-W23
python3 run_qbr.py --mock --cadence daily    --period 2026-06-07
```

---

## Live connections (v5 -- real Jira, Notion, Google Sheets)

### Prerequisites

**Jira**
- Atlassian account with a project
- API token from id.atlassian.com/manage-profile/security/api-tokens

**Notion**
- Notion account with a database named "Meeting Notes"
- Integration token from notion.so/my-integrations
- Share the database with the integration

**Google Sheets**
- Google Cloud project with Sheets API enabled
- Service account with Viewer role
- Credentials JSON downloaded locally
- Share your spreadsheet with the service account email

### Setup

Create `.env` in the project root (never commit this file):

```
JIRA_BASE_URL=https://yourname.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your-token
JIRA_PROJECT=AL

NOTION_TOKEN=ntn_your-token
NOTION_DATABASE_ID=your-database-id

GOOGLE_CREDENTIALS_JSON=/path/to/google_credentials.json
SHEETS_SPREADSHEET_ID=your-spreadsheet-id
OPENAI_API_KEY=sk-...
```

```bash
pip install aacp langchain-openai google-auth google-api-python-client python-dotenv
python3 run_qbr.py --live
```

### Notion database structure

Create a database with these properties:
```
Name          Title
Date          Date
Attendees     Text
Decisions     Text
Action Items  Text
Status        Select (Complete, In Progress, Not Started)
```

### Google Sheets structure

Two tabs: `EMEA` and `NAMER`

```
cc_id | cc_name | approved_annual_gbp | ytd_spend_gbp | owner | gl_code
```

---

## The AACP packets

All six hops use rule-based encoding at zero LLM cost:

```
FETCH|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:kpi_metrics|period:2026-Q1|src:jira|fmt:json
FETCH|HR|return:ORCHESTRATOR|p:2|aacp:1.1|res:meeting_notes|period:2026-Q1|src:notion|req:notes,decisions,action_items|fmt:json
FETCH|FIN|return:ORCHESTRATOR|p:2|aacp:1.1|res:budget_actuals|period:2026-Q1|src:sheets|regions:all|fmt:json
MERGE|FIN|return:ORCHESTRATOR|p:1|aacp:1.1|res:qbr_consolidated|period:2026-Q1|cadence:quarterly|rules:qbr_quarterly_v1|validate:completeness
BUILD|MKT|return:ORCHESTRATOR|p:2|aacp:1.1|res:qbr_narrative|period:2026-Q1|cadence:quarterly|audience:exec|req:summary,highlights,risks,recommendation,budget_flag
LOG|FIN|return:AUD-Agent|p:3|aacp:1.1|period:2026-Q1|cadence:quarterly|status:complete|actor:ORCHESTRATOR
```

---

## Human review gates

The narrative is a draft. AACP coordinates the data gathering and
consolidation. The final decisions remain with the human reviewer.

```
AI coordinates:   fetch metrics, extract notes, reconcile budget,
                  merge data, draft narrative

Human decides:    which accomplishments to highlight,
                  which risks to escalate,
                  whether to continue, pause, or scale a project
```

---

## Security notes

- Never commit `.env` or `google_credentials.json`
- Both are in `.gitignore`
- Google service account should have Viewer role only
- Rotate credentials immediately if accidentally exposed

---

## Lab progression

```
v3   Five workflows, four models, mock CSV data
     github.com/MackayAndrew/aacp-lab

v4   QBR workflow, realistic API data shapes, mock connectors
     Four cadences: daily, weekly, monthly, quarterly

v5   Live connections (this lab)
     Real Jira, Notion and Google Sheets
     Verified June 2026
```

---

## Links

- Protocol: https://aacp.dev
- IETF Draft: https://datatracker.ietf.org/doc/draft-mackay-aacp/
- Python SDK: https://github.com/MackayAndrew/aacp
- Community rules: https://registry.aacp.dev
- LangChain integration: https://github.com/MackayAndrew/aacp-langchain
- CrewAI integration: https://github.com/MackayAndrew/aacp-crewai
