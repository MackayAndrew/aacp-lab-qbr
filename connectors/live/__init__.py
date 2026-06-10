"""
Live connectors for QBR Lab v5.
Real API connections to Jira, Notion and Google Sheets.

Requires .env with:
    JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT
    NOTION_TOKEN, NOTION_DATABASE_ID
    GOOGLE_CREDENTIALS_JSON, SHEETS_SPREADSHEET_ID

pip install google-auth google-api-python-client
"""

from .jira_live   import LiveJiraClient
from .notion_live import LiveNotionClient
from .sheets_live import LiveSheetsClient

__all__ = ["LiveJiraClient", "LiveNotionClient", "LiveSheetsClient"]
