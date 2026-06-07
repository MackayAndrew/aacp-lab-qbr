"""
AACP QBR Lab v4
Quarterly Business Review workflow using AACP coordination.

Usage:
    # Mock data -- no API keys needed
    python3 run_qbr.py --mock

    # Specific cadence and period
    python3 run_qbr.py --mock --cadence quarterly --period 2026-Q1
    python3 run_qbr.py --mock --cadence monthly   --period 2026-03
    python3 run_qbr.py --mock --cadence weekly    --period 2026-W23
    python3 run_qbr.py --mock --cadence daily     --period 2026-06-07

    # Specific model
    python3 run_qbr.py --mock --model gpt-4.1

    # Live connections (v5 -- requires API keys)
    python3 run_qbr.py --live

Requires:
    pip install aacp langchain-openai
    export OPENAI_API_KEY=sk-...
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from encoders.qbr_encoder     import QBREncoder
from agents.metrics_agent     import MetricsAgent
from agents.notes_agent       import NotesAgent
from agents.budget_agent      import BudgetAgent
from agents.consolidate_agent import ConsolidateAgent
from agents.narrative_agent   import NarrativeAgent

try:
    from aacp.packet_bus import AACPPacketBus
except ImportError:
    # Inline minimal PacketBus if aacp not installed
    import json as _json
    import re as _re

    VALID_TASKS = {"FETCH","PROC","FLAG","RESOLVE","LOG","SEND",
                   "BUILD","MERGE","CALC","REPORT","ACK","SYNC"}
    VALID_DOMS  = {"HR","FIN","SALES","LEGAL","IT","CS","MKT"}

    def _validate(packet):
        fields = packet.strip().split("|")
        errors = []
        if len(fields) < 3: return False, ["Too few fields"]
        if fields[0] not in VALID_TASKS: errors.append(f"Unknown TASK: {fields[0]}")
        if fields[1] not in VALID_DOMS:  errors.append(f"Unknown DOM: {fields[1]}")
        keys = {f.split(":",1)[0].lower() for f in fields[2:] if ":" in f}
        if "return" not in keys: errors.append("Missing return:")
        if "aacp"   not in keys: errors.append("Missing aacp:")
        return len(errors) == 0, errors

    class AACPPacketBus:
        def __init__(self, **kwargs):
            self.hops      = []
            self.total_cost = 0.0

        def dispatch(self, from_agent, to_agent, packet, data=None, preview_fn=None):
            valid, errors = _validate(packet)
            response = to_agent.receive(packet, data or {})
            result   = response.get("result")
            cost     = response.get("cost_usd", 0.0)
            self.total_cost += cost
            tag = "✓" if valid and result else "✗"
            print(f"\n  {tag} [{from_agent}] -> [{to_agent.name}]")
            print(f"    {packet[:75]}")
            if not valid:
                print(f"    Schema: INVALID {errors}")
            else:
                print(f"    Schema: VALID  ${cost:.4f}")
            if preview_fn and result:
                try:
                    print(f"    -> {str(preview_fn(result))[:75]}")
                except Exception:
                    pass
            self.hops.append({"packet": packet, "valid": valid,
                              "cost_usd": cost})
            return result


class AuditAgent:
    name   = "AUDIT-AGENT"
    domain = "LOG"

    def receive(self, packet, data=None):
        return {"result": {"logged": True, "ts": time.time()},
                "tokens_in": 0, "tokens_out": 0,
                "latency_ms": 1, "cost_usd": 0.0, "error": None}


def run_qbr(model, period, cadence, mode, output_dir):
    enc = QBREncoder()

    if mode == "mock":
        from connectors.mock import MockJiraClient, MockNotionClient, MockSheetsClient
        jira_conn   = MockJiraClient(period=period)
        notion_conn = MockNotionClient(period=period)
        sheets_conn = MockSheetsClient(period=period)
    else:
        # v5 live connectors -- placeholder
        raise NotImplementedError(
            "Live connections coming in Lab v5. "
            "See connectors/live/ for setup instructions."
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    kw      = {"model": model, "api_key": api_key}

    metrics_agent     = MetricsAgent(jira_conn,   **kw)
    notes_agent       = NotesAgent(notion_conn,   **kw)
    budget_agent      = BudgetAgent(sheets_conn,  **kw)
    consolidate_agent = ConsolidateAgent(**kw)
    narrative_agent   = NarrativeAgent(**kw)
    audit_agent       = AuditAgent()

    bus = AACPPacketBus(
        workflow=f"qbr_{cadence}",
        model=model,
        audit_log=str(output_dir / f"audit_qbr_{period}.jsonl"),
        verbose=False,
    )

    print(f"\n{'='*60}")
    print(f"  AACP QBR Lab v4 -- {cadence.upper()}")
    print(f"  Period: {period}  |  Model: {model}  |  Mode: {mode}")
    print(f"{'='*60}")

    # Hop 1: Fetch metrics
    r1 = bus.dispatch("ORCHESTRATOR", metrics_agent,
        enc.fetch_metrics(period, sources=["jira"]).packet,
        None,
        lambda x: f"velocity avg: {x.get('velocity',{}).get('average','?')}, "
                  f"OKRs on track: {x.get('okr_summary',[{}])[0].get('on_track_count','?')}")

    # Hop 2: Fetch meeting notes
    r2 = bus.dispatch("ORCHESTRATOR", notes_agent,
        enc.fetch_meeting_notes(period, source="notion").packet,
        None,
        lambda x: f"{x.get('meeting_count',0)} meetings, "
                  f"{x.get('action_items',{}).get('complete',0)}/"
                  f"{x.get('action_items',{}).get('total',0)} actions complete")

    # Hop 3: Fetch budget
    r3 = bus.dispatch("ORCHESTRATOR", budget_agent,
        enc.fetch_budget(period, source="sheets").packet,
        None,
        lambda x: f"variance: {x.get('total_variance_pct',0):.1f}%, "
                  f"status: {x.get('overall_status','?')}")

    # Hop 4: Consolidate
    r4 = bus.dispatch("ORCHESTRATOR", consolidate_agent,
        enc.consolidate(period, cadence=cadence).packet,
        {"metrics": r1, "notes": r2, "budget": r3},
        lambda x: f"{len(x.get('cross_references',[]))} cross-references found")

    # Hop 5: Build narrative (human review required after this)
    r5 = bus.dispatch("ORCHESTRATOR", narrative_agent,
        enc.build_narrative(period, cadence=cadence, audience="exec").packet,
        {"consolidated": r4},
        lambda x: (str(x.get("executive_summary",""))[:65]
                   if isinstance(x.get("executive_summary"), str)
                   else f"recommendation: {x.get('recommendation',{}).get('action','?')}"))

    # Hop 6: Audit (deterministic, $0.00)
    bus.dispatch("ORCHESTRATOR", audit_agent,
        enc.log_run(period, cadence=cadence).packet,
        {"period": period, "cadence": cadence},
        lambda x: "Audit record written")

    # Compute totals
    try:
        total_cost   = bus.result.total_cost
        total_tokens = bus.result.total_tokens
        hop_count    = len(bus.result.hops)
    except AttributeError:
        total_cost   = bus.total_cost
        total_tokens = sum(h.get("tokens_in", 0) for h in bus.hops)
        hop_count    = len(bus.hops)

    print(f"\n{'─'*60}")
    print(f"  COMPLETE -- {cadence.upper()} QBR")
    print(f"  Hops:    {hop_count}")
    print(f"  Tokens:  {total_tokens:,}")
    print(f"  Cost:    ${total_cost:.4f}")
    print(f"{'─'*60}")

    # Print narrative summary
    if r5:
        print(f"\n  EXECUTIVE SUMMARY:")
        summary = r5.get("executive_summary", "")
        if summary:
            for line in str(summary)[:400].split(". "):
                if line.strip():
                    print(f"  {line.strip()}.")
        rec = r5.get("recommendation", {})
        if rec:
            print(f"\n  RECOMMENDATION: {rec.get('action','?').upper()}")
            print(f"  {rec.get('rationale','')[:100]}")

    # Save output
    output_dir.mkdir(exist_ok=True)
    ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"qbr_{cadence}_{period}_{ts}.json"
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cadence":   cadence,
            "period":    period,
            "model":     model,
            "mode":      mode,
            "hops":      hop_count,
            "cost_usd":  total_cost,
            "metrics":   r1,
            "notes":     r2,
            "budget":    r3,
            "consolidated": r4,
            "narrative": r5,
        }, f, indent=2)

    print(f"\n  Saved: {out_path}")
    print(f"\n  NOTE: Human review required before presenting.")
    print(f"  The narrative is a draft. Verify all figures.")
    print(f"  Recommendation is AI-assisted, not AI-decided.")

    return r5


def main():
    parser = argparse.ArgumentParser(
        description="AACP QBR Lab v4 -- Business review workflow"
    )
    parser.add_argument("--mock",    action="store_true",
                        help="Use mock data (no API keys for Jira/Notion/Sheets)")
    parser.add_argument("--live",    action="store_true",
                        help="Use live connections (requires service API keys)")
    parser.add_argument("--cadence", default="quarterly",
                        choices=["daily","weekly","monthly","quarterly"])
    parser.add_argument("--period",  default="2026-Q1",
                        help="Period: 2026-Q1 / 2026-03 / 2026-W23 / 2026-06-07")
    parser.add_argument("--model",   default="gpt-4.1-mini",
                        choices=["gpt-4.1-mini","gpt-4.1","gpt-4o","gpt-4o-mini"])
    parser.add_argument("--output",  default="output")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: set OPENAI_API_KEY before running")
        sys.exit(1)

    if not args.mock and not args.live:
        print("Specify --mock or --live")
        sys.exit(1)

    mode = "mock" if args.mock else "live"
    run_qbr(
        model=args.model,
        period=args.period,
        cadence=args.cadence,
        mode=mode,
        output_dir=Path(args.output),
    )


if __name__ == "__main__":
    main()
