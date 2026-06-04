# Communication

> How the Main Agent communicates with all peer agents via IAMQ. The Main Agent is the central orchestrator — hub in a hub-and-spoke topology.

## IAMQ Registration

The agent registers on startup at `$IAMQ_BASE_URL`.

```json
{
  "agent_id": "main",
  "capabilities": [
    "orchestration",
    "monitoring",
    "dispatch",
    "user_relay"
  ]
}
```

## Elixir IAMQ Sidecar

The Main Agent uses the Elixir IAMQ sidecar service (in the `iamq/`
directory, run as the `iamq:` Docker service) to communicate with IAMQ.
The sidecar uses the shared `IamqSidecar.MqClient` and
`IamqSidecar.MqWsClient` from
[`openclaw-shared-base/iamq_sidecar`](https://github.com/r3dlex/openclaw-shared-base).

Available operations:

| Function | Purpose |
|----------|---------|
| `register` | Register `main` with IAMQ on startup |
| `heartbeat` | Send periodic heartbeat to maintain presence |
| `send_message` | Send a message to a specific agent or broadcast |
| `broadcast` | Broadcast a message to all agents |
| `inbox` | Fetch unread messages from the main agent's inbox |
| `ack` | Mark a message as read/processed |
| `agents` | Discover all registered agents and their capabilities |
| `status` | Check IAMQ service health |

## Incoming Messages

The Main Agent receives reports from all agents in the swarm:

| From | Message Type | Content |
|------|-------------|---------|
| `mail_agent` | Tidy reports | Email cleanup summaries, folder stats |
| `gitrepo_agent` | PR evaluations, weekly reports, security alerts | Scoring results, repo status |
| `journalist_agent` | Briefing announcements | News/weather briefing summaries |
| `instagram_agent` | Engagement reports, error alerts, cooldowns | Cycle results, API status |
| `librarian_agent` | Status reports, search results | Vault health, document metadata |
| `broadcast` | All agent broadcasts | Swarm-wide announcements |

## Outgoing Messages

### Dispatch to Specific Agent

```json
{
  "from": "main",
  "to": "librarian_agent",
  "type": "request",
  "priority": "NORMAL",
  "subject": "search: quarterly revenue",
  "body": "Find documents related to quarterly revenue reports from Q1 2026."
}
```

### Status Query

```json
{
  "from": "main",
  "to": "gitrepo_agent",
  "type": "request",
  "priority": "NORMAL",
  "subject": "repo-status",
  "body": "Current sync status for all monitored repositories."
}
```

## Message Processing Loop

On each heartbeat cycle:

1. `poll_inbox` — fetch unread messages
2. Route by sender and type:
   - Error/urgent messages → escalate to user via Telegram
   - Status reports → log and summarize
   - Responses to prior requests → correlate and relay to user
3. `mark_message` — mark processed messages as read

## Peer Agents

| Agent | Relationship |
|-------|-------------|
| `mail_agent` | Receives tidy reports and health updates |
| `gitrepo_agent` | Receives PR scores, weekly reports, security alerts |
| `journalist_agent` | Receives briefing announcements |
| `instagram_agent` | Receives engagement reports, error alerts |
| `librarian_agent` | Sends search/summarize requests, receives results |
| `broadcast` | Monitors all swarm-wide announcements |

## User Relay

The Main Agent bridges IAMQ and the user's Telegram:

- **IAMQ → Telegram:** Critical errors, security alerts, and requested reports are forwarded to the user
- **Telegram → IAMQ:** User commands that target a specific agent are dispatched via IAMQ

Telegram is for humans. IAMQ is for agents. Never substitute one for the other.

## Related

- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Safety: [SAFETY.md](SAFETY.md)
- Testing: [TESTING.md](TESTING.md)
- [IAMQ HTTP API](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/API.md)
- [IAMQ Cron Scheduling](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/CRON.md)
- [IAMQ Sidecar Client (iamq_sidecar)](https://github.com/r3dlex/openclaw-inter-agent-message-queue/tree/main/sidecar)

---
*Owner: main*
