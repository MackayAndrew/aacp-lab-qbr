"""
connectors/live/notion_live.py
Real Notion API connector for QBR Lab v5.
Mirrors MockNotionClient interface exactly.

Setup:
    .env file with:
    NOTION_TOKEN=ntn_your-token
    NOTION_DATABASE_ID=your-database-id
"""

import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/ubuntu/aacp-lab-qbr/.env")


class LiveNotionClient:
    """
    Real Notion API client.
    Same interface as MockNotionClient -- agents do not change.
    """

    NOTION_VERSION = "2022-06-28"

    def __init__(self, database_id=None, period="2026-Q1"):
        self.database_id = database_id or os.environ["NOTION_DATABASE_ID"]
        self.period      = period
        self.token       = os.environ["NOTION_TOKEN"]
        self.headers     = {
            "Authorization":  f"Bearer {self.token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type":   "application/json",
        }

    def _query(self, database_id, body=None):
        url  = f"https://api.notion.com/v1/databases/{database_id}/query"
        data = json.dumps(body or {}).encode()
        req  = urllib.request.Request(url, data=data,
                                      headers=self.headers, method="POST")
        try:
            raw = urllib.request.urlopen(req).read()
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            print(f"  Notion API error {e.code}: {e.read().decode()[:150]}")
            return None

    def _text(self, prop):
        """Extract plain text from a Notion property."""
        if not prop:
            return ""
        ptype = prop.get("type")
        if ptype == "title":
            return " ".join(t.get("plain_text","") for t in prop.get("title",[]))
        if ptype == "rich_text":
            return " ".join(t.get("plain_text","") for t in prop.get("rich_text",[]))
        if ptype == "date":
            d = prop.get("date")
            return d.get("start","") if d else ""
        if ptype == "select":
            s = prop.get("select")
            return s.get("name","") if s else ""
        return ""

    def get_meeting_notes(self, period=None):
        """
        Query Notion database and return meeting notes.
        Returns data in the same shape as MockNotionClient.
        """
        result = self._query(self.database_id)
        if not result:
            return self._empty_notes(period)

        meetings = []
        for page in result.get("results", []):
            props = page.get("properties", {})

            title      = self._text(props.get("Name"))
            date       = self._text(props.get("Date"))
            attendees  = self._text(props.get("Attendees"))
            decisions  = self._text(props.get("Decisions"))
            action_items = self._text(props.get("Action Items"))
            status     = self._text(props.get("Status"))

            if not title:
                continue

            # Parse attendees into list
            attendee_list = [a.strip() for a in attendees.split(",")
                           if a.strip()] if attendees else []

            # Parse decisions into list
            decision_list = [d.strip() for d in decisions.split(".")
                           if d.strip() and len(d.strip()) > 5]

            # Parse action items into structured list
            action_list = []
            if action_items:
                for item in action_items.split("."):
                    item = item.strip()
                    if item and len(item) > 5:
                        action_list.append({
                            "action": item,
                            "owner":  attendee_list[0] if attendee_list else "TBC",
                            "due":    date,
                            "status": status.lower() if status else "not_started",
                        })

            meetings.append({
                "date":         date,
                "title":        title,
                "attendees":    attendee_list,
                "decisions":    decision_list,
                "action_items": action_list,
                "status":       status,
            })

        # Sort by date
        meetings.sort(key=lambda x: x.get("date",""))

        return {
            "source":        "notion_live",
            "database":      self.database_id,
            "period":        period or self.period,
            "meetings":      meetings,
            "meeting_count": len(meetings),
        }

    def get_action_items(self, period=None, status=None):
        """Returns action items, optionally filtered by status."""
        notes  = self.get_meeting_notes(period)
        items  = []
        for meeting in notes.get("meetings", []):
            for item in meeting.get("action_items", []):
                if status is None or item.get("status") == status:
                    items.append({**item, "meeting_date": meeting["date"],
                                  "meeting_title": meeting["title"]})
        return {
            "source": "notion_live",
            "period": period or self.period,
            "status": status,
            "items":  items,
            "count":  len(items),
        }

    def _empty_notes(self, period):
        return {
            "source": "notion_live", "database": self.database_id,
            "period": period or self.period,
            "meetings": [], "meeting_count": 0,
        }


if __name__ == "__main__":
    client = LiveNotionClient()
    notes  = client.get_meeting_notes()
    print(json.dumps(notes, indent=2))
