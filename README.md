# AACP QBR Lab v4

**Quarterly Business Review workflow using AACP coordination.**

Five agents. Six coordination hops. Real business data shapes.
AACP packets coordinate the agents throughout. Zero coordination LLM cost.

---

## What this demonstrates

A QBR workflow that reflects how a real business review is assembled:

1. **MetricsAgent** fetches sprint velocity, OKR progress and bug metrics from Jira
2. **NotesAgent** extracts decisions and action items from Notion meeting notes
3. **BudgetAgent** retrieves actuals vs budget from Google Sheets
4. **ConsolidateAgent** merges all three sources into a single coherent view
5. **NarrativeAgent** drafts the executive summary for human review
6. **AuditAgent** writes a structured audit record at zero LLM cost

All six coordination hops use AACP packets. The agents receive typed,
validated instructions -- not natural language descriptions that vary
on every run.

---

## The cadence hierarchy

The same workflow and the same encoder work at every review cadence.
Only the `period` field and the narrative depth change.

| Cadence | Period format | Narrative depth |
|---|---|---|
| Daily | 2026-06-07 | Anomalies and blockers only |
| Weekly | 2026-W23 | Progress, risks, blockers |
| Monthly | 2026-03 | Summary, highlights, budget flag |
| Quarterly | 2026-Q1 | Full narrative with recommendation |

---

## Quick start

```bash
# Install dependencies
pip install aacp langchain-openai

# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Run quarterly review with mock data (no Jira/Notion/Sheets needed)
python3 run_qbr.py --mock

# Run with a specific cadence
python3 run_qbr.py --mock --cadence monthly --period 2026-03
python3 run_qbr.py --mock --cadence weekly  --period 2026-W23
python3 run_qbr.py --mock --cadence daily   --period 2026-06-07

# Run with a specific model
python3 run_qbr.py --mock --model gpt-4.1
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

## v4 vs v5

| Feature | v4 (this lab) | v5 (coming) |
|---|---|---|
| Data sources | Realistic mock data | Live Jira, Notion, Google Sheets |
| API keys needed | OpenAI only | OpenAI + Jira + Notion + Sheets |
| Reproducible | Yes -- same output every run | Depends on real data |
| Community runnable | Yes | Requires service account setup |

See `connectors/live/` for v5 setup instructions when available.

---

## Human review gates

The narrative is a draft. AACP coordinates the data gathering and
consolidation. The final decisions remain with the human reviewer.

```
AI coordinates:    fetch metrics, extract notes, reconcile budget,
                   merge data, draft narrative

Human decides:     which accomplishments to highlight,
                   which risks to escalate,
                   whether to continue, pause, or scale a project
```

This is the honest scope of the tool. See the output files for
the full structured results including the recommendation rationale.

---

## Lab progression

```
v3  Five workflows, four models, mock CSV data
    github.com/MackayAndrew/aacp-lab

v4  QBR workflow, realistic API data shapes (this lab)
    Mock connectors for Jira, Notion, Google Sheets
    Four cadences: daily, weekly, monthly, quarterly

v5  Live connections
    Real Jira REST API, Notion API, Google Sheets API
    Instructions in connectors/live/
```

---

## Links

- Protocol: https://aacp.dev
- IETF Draft: https://datatracker.ietf.org/doc/draft-mackay-aacp/
- Python SDK: https://github.com/MackayAndrew/aacp
- Community rules: https://registry.aacp.dev
