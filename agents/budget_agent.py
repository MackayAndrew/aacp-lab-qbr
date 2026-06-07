"""
BudgetAgent
Fetches and reconciles budget actuals from financial systems.
Receives FETCH|FIN|res:budget_actuals AACP packets.
"""

import json
import os
import re
import time


SYSTEM_PROMPT = """You are Budget-Agent. You understand AACP v1.1 coordination packets.

When you receive a FETCH|FIN|res:budget_actuals packet, process the provided
budget data and return a consolidated financial summary.

Always return valid JSON only. No markdown fences. No preamble.
Pre-compute all numeric values. Never write arithmetic expressions in JSON.

Expected output shape:
{
  "period": "2026-Q1",
  "source": "sheets",
  "regions": ["EMEA", "NAMER"],
  "total_approved": 0,
  "total_actual": 0,
  "total_variance": 0,
  "total_variance_pct": 0.0,
  "material_variances": [
    {"region": "string", "dept": "string", "variance_pct": 0.0, "flag": "string"}
  ],
  "overall_status": "on_budget|over_budget|under_budget"
}
"""

class BudgetAgent:
    name   = "BUDGET-AGENT"
    domain = "FIN"

    def __init__(self, connector, model="gpt-4.1-mini", api_key=None):
        self.connector = connector
        self.model     = model
        self.api_key   = api_key or os.environ.get("OPENAI_API_KEY")

    def receive(self, packet: str, data: dict = None) -> dict:
        raw_data = self.connector.get_budget_actuals()
        prompt   = f"Coordination packet:\n{packet}\n\nBudget data:\n{json.dumps(raw_data, indent=2)}\n\nReturn valid JSON only. Pre-compute all numbers."

        start = time.time()
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOpenAI(model=self.model, api_key=self.api_key,
                             max_tokens=1500, temperature=0)
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
