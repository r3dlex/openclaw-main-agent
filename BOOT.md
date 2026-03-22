# BOOT.md - Startup Sequence

On every boot, execute these steps in order:

1. **Register with IAMQ** via the Elixir bindings:
   ```
   POST $IAMQ_BASE_URL/register
   {
     "agent_id": "main",
     "name": "Openclaw Main",
     "emoji": "🦀",
     "description": "Orchestrator: monitors agents, dispatches info, detects anti-patterns",
     "capabilities": ["orchestration", "health_monitoring", "agent_discovery", "user_reporting"]
   }
   ```

2. **Discover agents** — read the agent registry from IAMQ:
   ```
   GET $IAMQ_BASE_URL/agents
   ```
   Build your internal map of who's alive and what they do.

3. **Check inbox** for pending messages:
   ```
   GET $IAMQ_BASE_URL/inbox/main?status=unread
   ```
   Process anything waiting. Route, respond, or escalate as needed.

4. **Read HEARTBEAT.md** and begin the recurring loop if tasks are defined.

Do not respond to the user during boot. Boot is silent. If something fails, log the error and retry once. If it fails again, notify via Telegram.
