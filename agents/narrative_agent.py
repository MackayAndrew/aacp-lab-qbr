"""
NarrativeAgent
Drafts the narrative section for the review pack.
Receives BUILD|MKT|res:qbr_narrative AACP packets.
This is the LLM task layer -- the agent does real reasoning work.
No external connections needed.
"""

import json
import os
import re
import time


SYSTEM_PROMPTS = {
    "daily": """You are Narrative-Agent. Draft a brief daily anomaly report.
Focus on: what changed, what is blocked, what needs immediate attention.
Return valid JSON only. No markdown fences.

Output shape:
{
  "executive_summary": "1 paragraph summary string",
  "anomalies": ["string"],
  "blockers": ["string"],
  "actions_needed": ["string"]
}""",

    "weekly": """You are Narrative-Agent. Draft a weekly progress summary.
Focus on: progress vs targets, risks emerging, blockers to resolve.
Return valid JSON only. No markdown fences.

Output shape:
{
  "executive_summary": "1-2 paragraph narrative string",
  "highlights": ["string"],
  "blockers": ["string"],
  "risks": [{"risk": "string", "severity": "high|medium|low"}]
}""",

    "monthly": """You are Narrative-Agent. Draft a monthly management summary.
Focus on: progress vs plan, budget status, team health, risks.
Return valid JSON only. No markdown fences.

Output shape:
{
  "executive_summary": "2 paragraph narrative string",
  "highlights": ["string"],
  "risks": [{"risk": "string", "severity": "high|medium|low"}],
  "budget_headline": "string",
  "actions_summary": {"complete": 0, "in_progress": 0, "overdue": 0}
}""",

    "quarterly": """You are Narrative-Agent. Draft a quarterly executive summary.
This will be presented by a senior manager to leadership.
Focus on: strategic progress, key accomplishments, risks, budget, clear recommendation.
Be direct. Do not hedge. The recommendation must be explicit.
Return valid JSON only. No markdown fences.

Output shape:
{
  "executive_summary": "2-3 paragraph narrative string",
  "key_accomplishments": ["string"],
  "risks": [{"risk": "string", "severity": "high|medium|low", "mitigation": "string"}],
  "budget_headline": "string",
  "recommendation": {"action": "continue|pause|scale|pivot", "rationale": "string"},
  "next_quarter_focus": ["string"]
}"""
}


class NarrativeAgent:
    name   = "NARRATIVE-AGENT"
    domain = "MKT"

    def __init__(self, model="gpt-4.1-mini", api_key=None):
        self.model   = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def receive(self, packet: str, data: dict = None) -> dict:
        cadence = "quarterly"
        if "cadence:" in packet:
            for field in packet.split("|"):
                if field.startswith("cadence:"):
                    cadence = field.split(":", 1)[1]

        system = SYSTEM_PROMPTS.get(cadence, SYSTEM_PROMPTS["quarterly"])
        prompt = f"Coordination packet:\n{packet}\n\nConsolidated QBR data:\n{json.dumps(data or {}, indent=2)}\n\nReturn valid JSON only."

        start = time.time()
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOpenAI(model=self.model, api_key=self.api_key,
                             max_tokens=2000, temperature=0)
            resp = llm.invoke([SystemMessage(content=system),
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
