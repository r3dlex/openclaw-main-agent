# Executive Daily & Weekly Briefer

## Purpose
Aggregate calendar data + outstanding tasks from Email/Teams/Instagram agents into concise, actionable briefings.

## Data sources
- Calendar: user’s full agenda (preferred interface TBD: Outlook calendar / Workday / Google Calendar)
- Pending queues: action items exported by:
  - Email agent
  - Teams analyst
  - Instagram manager

## Canonical queue files (workspace)
These are the handoff contracts between agents.

- Email: `briefing/queues/email.json`
- Teams: `briefing/queues/teams.json`
- Instagram: `briefing/queues/instagram.json`

Schema (all three):
```json
{
  "updatedAt": "ISO-8601",
  "items": [
    {
      "id": "string",
      "source": "string",
      "priority": "URGENT|HIGH|NORMAL|LOW",
      "summary": "string",
      "link": "string|null",
      "needsApproval": true,
      "draft": "string|null",
      "createdAt": "ISO-8601"
    }
  ]
}
```

Agents should update their queue file every run.

## Routines

### 1) Weekly Strategy Lookahead
- Trigger: Sunday 20:00 Europe/Berlin
- Scope: next Monday–Sunday
- Actions:
  - Review week calendar
  - Highlight high-impact events (VIPs, board meetings, deadlines)
  - Flag conflicts/double-bookings
  - Flag days with >6h meetings

### 2) Daily Tactical Briefing
- Trigger: daily 06:00 Europe/Berlin
- Scope: today 00:00–23:59
- Actions:
  - Print agenda chronologically
  - Action Items:
    - Email: top 3 unread/pending VIP emails (from email queue)
    - Teams: pending actions/urgent DMs (from teams queue)
    - Social: approvals waiting (from instagram queue)
  - Context linking: if meeting attendee is VIP/Important, attach recent related item links.

## Output format
Use the user-provided template (emoji ok in output as given).

## Constraints
- Do not send replies on any channel. Only summarize + draft for approval.
- If calendar/queues are unavailable, report what’s missing and how to fix (attach tab / enable access).
