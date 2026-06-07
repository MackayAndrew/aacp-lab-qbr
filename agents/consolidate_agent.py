"""
ConsolidateAgent
Merges metrics, notes and budget into a single QBR view.
Receives MERGE|FIN|res:qbr_consolidated AACP packets.
No external connections -- works on agent outputs only.
"""

import json
import os
import re
import time


SYSTEM_PROMPT = """You are Consolidate-Agent. You understand AACP v1.1 coordination packets.

When you receive a MERGE|FIN|res:qbr_consolidated packet, merge the provided
metrics, notes and budget data into a single consolidated QBR summary.

Always return valid JSON only. No markdown fences. No preamble.
Pre-compute all numeric values.

Expected output shape:
{
  "period": "2026-Q1",
  "cadence": "quarterly",
  "metrics_summary": {},
  "notes_summary": {},
  "budget_summary": {},
  "cross_references": [
    {"finding": "string", "source": "metrics|notes|budget", "significance": "high|medium|low"}
  ],
  "headline_numbers": {
    "avg_velocity": 0,
    "okrs_on_track": 0,
    "okrs_total": 0,
    "budget_variance_pct": 0.0,
    "actions_complete": 0,
    "actions_total": 0
  }
}
"""

class ConsolidateAgent:
    name   = "CONSOLIDATE-AGENT"
    domain = "FIN"

    def __init__(self, model="gpt-4.1-mini", api_key=None):
        self.model   = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def receive(self, packet: str, data: dict = None) -> dict:
        prompt = f"Coordination packet:\n{packet}\n\nData to consolidate:\n{json.dumps(data or {}, indent=2)}\n\nReturn valid JSON only."

        start = time.time()
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOpenAI(model=self.model, api_key=self.api_key,
                             max_tokens=2000, temperature=0)
            resp = llm.invoke([SystemMessage(content=SYSTEM_PROMPT),
                               HumanMessage(content=prompt)])
            latency = (time.time() - start) * 1000

            raw = re.sub(r"^```(?:json)?\s*", "", resp.content.strip())
            raw = re.sub(r"\s*```$", "", raw)
            result = json.loads(raw.strip())

            tu = resp.response_metadata.get("token_usage", {})
            ti = tu.get("prompt_tokens", 0)
            to = tu.get("completion_tokens", 0)
            cost = (ti + to) / 1_000_000 * 0.40

            return {"result": result, "tokens_in": ti, "tokens_out": to,
                    "latency_ms": round(latency, 0),
                    "cost_usd": round(cost, 6), "error": None}
        except Exception as e:
            return {"result": None, "tokens_in": 0, "tokens_out": 0,
                    "latency_ms": round((time.time()-start)*1000, 0),
                    "cost_usd": 0.0, "error": str(e)}
