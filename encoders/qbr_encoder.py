"""
QBREncoder
AACP encoder for Quarterly Business Review workflows.

The same encoder works at every cadence by changing the period field:
  Daily:     period="2026-06-07"
  Weekly:    period="2026-W23"
  Monthly:   period="2026-05"
  Quarterly: period="2026-Q1"

Usage:
    from encoders.qbr_encoder import QBREncoder

    enc = QBREncoder()
    pkt = enc.fetch_metrics("2026-Q1", sources=["jira"])
    print(pkt.packet)
    print(f"Cost: ${pkt.api_cost_usd:.2f}")  # $0.00
"""

from dataclasses import dataclass


@dataclass
class QBRPacket:
    packet:       str
    task:         str
    domain:       str
    period:       str
    api_cost_usd: float = 0.0
    encoder_type: str   = "rule_based"

    def __str__(self):
        return self.packet


class QBREncoder:
    """
    Deterministic encoder for QBR coordination packets.
    Zero LLM cost. Identical output for identical input.

    Works at all cadences: daily, weekly, monthly, quarterly.
    Add QBREncoder to the AACP community registry as the
    canonical encoder for planning and reporting workflows.
    """

    VERSION      = "1.1"
    RETURN_AGENT = "ORCHESTRATOR"

    def _pkt(self, task, dom, fields: dict) -> QBRPacket:
        """Build a validated AACP packet from fields dict."""
        named = "|".join(f"{k}:{v}" for k, v in fields.items())
        packet = f"{task}|{dom}|{named}"
        period = fields.get("period", "")
        return QBRPacket(
            packet=packet, task=task, domain=dom,
            period=period, api_cost_usd=0.0,
        )

    # ── Fetch hops ─────────────────────────────────────────────────────────

    def fetch_metrics(self, period: str, sources: list = None) -> QBRPacket:
        """
        Fetch KPI and OKR metrics from project trackers.
        Default sources: jira. Add asana, monday as needed.

        Period examples:
          "2026-Q1"   quarterly
          "2026-05"   monthly
          "2026-W23"  weekly
          "2026-06-07" daily
        """
        src = ",".join(sources) if sources else "jira"
        return self._pkt("FETCH", "FIN", {
            "return":  self.RETURN_AGENT,
            "p":       "1",
            "aacp":    self.VERSION,
            "res":     "kpi_metrics",
            "period":  period,
            "src":     src,
            "fmt":     "json",
        })

    def fetch_meeting_notes(self, period: str, source: str = "notion") -> QBRPacket:
        """
        Fetch meeting notes and extract action items.
        Default source: notion. Switch to confluence, teams as needed.
        """
        return self._pkt("FETCH", "HR", {
            "return":  self.RETURN_AGENT,
            "p":       "2",
            "aacp":    self.VERSION,
            "res":     "meeting_notes",
            "period":  period,
            "src":     source,
            "req":     "notes,decisions,action_items",
            "fmt":     "json",
        })

    def fetch_budget(self, period: str, regions: list = None,
                     source: str = "sheets") -> QBRPacket:
        """
        Fetch budget actuals vs plan from financial systems.
        Default source: sheets. Switch to netsuite, quickbooks as needed.
        """
        reg = ",".join(regions) if regions else "all"
        return self._pkt("FETCH", "FIN", {
            "return":  self.RETURN_AGENT,
            "p":       "2",
            "aacp":    self.VERSION,
            "res":     "budget_actuals",
            "period":  period,
            "src":     source,
            "regions": reg,
            "fmt":     "json",
        })

    # ── Consolidate hop ────────────────────────────────────────────────────

    def consolidate(self, period: str, cadence: str = "quarterly") -> QBRPacket:
        """
        Merge metrics, notes, and budget into a single consolidated view.
        Deduplicates action items, aligns budget to common currency.
        """
        return self._pkt("MERGE", "FIN", {
            "return":  self.RETURN_AGENT,
            "p":       "1",
            "aacp":    self.VERSION,
            "res":     "qbr_consolidated",
            "period":  period,
            "cadence": cadence,
            "rules":   f"qbr_{cadence}_v1",
            "validate": "completeness",
        })

    # ── Narrative hop ──────────────────────────────────────────────────────

    def build_narrative(self, period: str, cadence: str = "quarterly",
                        audience: str = "exec") -> QBRPacket:
        """
        Draft the narrative section for the review pack.
        Cadence adjusts depth: daily=anomalies only, quarterly=full narrative.
        Audience adjusts tone: exec=strategic, board=governance.
        """
        req_map = {
            "daily":     "anomalies,blockers",
            "weekly":    "progress,risks,blockers",
            "monthly":   "summary,highlights,risks,budget_flag",
            "quarterly": "summary,highlights,risks,recommendation,budget_flag",
        }
        return self._pkt("BUILD", "MKT", {
            "return":   self.RETURN_AGENT,
            "p":        "2",
            "aacp":     self.VERSION,
            "res":      "qbr_narrative",
            "period":   period,
            "cadence":  cadence,
            "audience": audience,
            "req":      req_map.get(cadence, "summary,highlights,risks"),
        })

    # ── Audit hop ──────────────────────────────────────────────────────────

    def log_run(self, period: str, cadence: str = "quarterly",
                status: str = "complete") -> QBRPacket:
        """Write structured audit record. Deterministic. Zero LLM cost."""
        return self._pkt("LOG", "FIN", {
            "return":  "AUD-Agent",
            "p":       "3",
            "aacp":    self.VERSION,
            "period":  period,
            "cadence": cadence,
            "status":  status,
            "actor":   "ORCHESTRATOR",
        })
