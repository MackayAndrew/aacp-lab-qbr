"""
NotesAgent
Fetches and processes meeting notes and action items.
Receives FETCH|HR|res:meeting_notes AACP packets.
"""

import json
import os
import re
import time


SYSTEM_PROMPT = """You are Notes-Agent. You understand AACP v1.1 coordination packets.

When you receive a FETCH|HR|res:meeting_notes packet, process the provided
meeting notes and return a structured summary of decisions and action items.

Always return valid JSON only. No markdown fences. No preamble.

Expected output shape:
{
  "period": "2026-Q1",
  "source": "notion",
  "meeting_count": 3,
  "key_decisions": ["string"],
  "action_items": {
    "total": 8,
    "complete": 6,
    "in_progress": 2,
    "overdue": 0,
    "items": [{"owner": "string", "action": "string", "due": "date", "status": "string"}]
  },
  "themes": ["string"]
}
"""

class NotesAgent:
    name   = "NOTES-AGENT"
    domain = "HR"

    def __init__(self, connector, model="gpt-4.1-mini", api_key=None):
        self.connector = connector
        self.model     = model
        self.api_key   = api_key or os.environ.get("OPENAI_API_KEY")

    def receive(self, packet: str, data: dict = None) -> dict:
        raw_data = self.connector.get_meeting_notes()
        prompt   = f"Coordination packet:\n{packet}\n\nMeeting notes:\n{json.dumps(raw_data, indent=2)}\n\nReturn valid JSON only."

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
