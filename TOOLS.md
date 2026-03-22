# TOOLS.md - Available Integrations

### IAMQ API (via Elixir bindings)

Full CRUD operations per IAMQ spec/API.md:
- Register → `POST /register`
- Heartbeat → `POST /heartbeat`
- Send message → `POST /send`
- Poll inbox → `GET /inbox/:agent_id`
- Update message → `PATCH /messages/:id`
- List agents → `GET /agents`
- Agent details → `GET /agents/:agent_id`
- System health → `GET /status`

Connection: `$IAMQ_BASE_URL` (default http://127.0.0.1:18790)

### arch-cli

Architecture decision records and documentation management.
- Run via: `docker compose run arch-cli <command>`
- ADRs stored in `.archgate/adrs/`
- Create ADR: `docker compose run arch-cli new "Decision Title"`
- List ADRs: `docker compose run arch-cli list`

### Telegram

User-facing notifications only. Not for agent-to-agent communication.
- Bot token: `$TELEGRAM_BOT_TOKEN`
- Chat ID: `$TELEGRAM_CHAT_ID`
- Use for: anomaly reports, status summaries, escalation alerts

### Filesystem Observation

Monitor `$OPENCLAW_AGENTS_WORKSPACE_DIR` for:
- Agent health signals (heartbeat files, error logs)
- New agent registrations (new repo directories)
- Stale or crashed agents (no recent activity)
