"""
connectors/live/
Real API connectors for QBR lab v5.
Each client mirrors the mock connector interface exactly.
Replace Mock*Client with Live*Client without changing agent code.

Setup required:
  Jira:   JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
  Notion: NOTION_TOKEN, NOTION_DATABASE_ID
  Sheets: GOOGLE_CREDENTIALS_JSON, SHEETS_SPREADSHEET_ID

See README.md section "Live connections (v5)" for setup instructions.

Files in this directory:
  jira_live.py     -- Real Jira REST API (v3)
  notion_live.py   -- Real Notion API (2022-06-28)
  sheets_live.py   -- Real Google Sheets API v4

Coming in Lab v5.
"""
