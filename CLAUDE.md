# CLAUDE.md

Openclaw Main Agent — the orchestrator present in every Openclaw installation. Monitors all other agents via IAMQ, dispatches information to the user via Telegram, and documents inter-agent interactions. Performs no direct actions.

## Running Locally

Prerequisites: Docker or Podman. Nothing else.

```bash
cp .env.example .env
# Fill in your values in .env
docker compose build
docker compose up
```

## Environment Variables

See `.env.example` for all required variables. Key ones:

- `IAMQ_BASE_URL` — IAMQ server URL (default: http://127.0.0.1:18790)
- `OPENCLAW_AGENTS_WORKSPACE_DIR` — path to the agents workspace
- `AGENT_ID` — always `main` for this agent
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — user notification channel

## Project Structure

```
├── IDENTITY.md, SOUL.md, BOOT.md,     # Openclaw templates (agent reads these)
│   BOOTSTRAP.md, HEARTBEAT.md, TOOLS.md
├── AGENTS.md                           # Agent self-reference
├── spec/                               # Developer reference docs
│   ├── ARCHITECTURE.md                 # System architecture + ADR links
│   ├── LEARNINGS.md                    # Operational learnings
│   ├── TROUBLESHOOTING.md              # Known issues + fixes
│   ├── TESTING.md                      # How to run tests
│   └── PIPELINES.md                    # CI/CD documentation
├── tools/
│   ├── iamq_bindings/                  # Elixir IAMQ client
│   ├── pipeline_runner/                # Python CI/CD module
│   └── arch-cli/                       # Containerized arch-cli
├── .archgate/adrs/                     # Architecture Decision Records
├── scripts/                            # Operational scripts
├── cron/                               # Cron definitions
└── .github/workflows/                  # CI/CD pipelines
```

## Common Commands

All commands run inside containers:

```bash
# Run Elixir tests
docker compose run iamq_bindings mix test

# Run Python tests
docker compose run pipeline_runner poetry run pytest

# Manage ADRs
docker compose run arch-cli new "Decision Title"
docker compose run arch-cli list

# Run pipeline stages
docker compose run pipeline_runner poetry run pipeline-runner lint
docker compose run pipeline_runner poetry run pipeline-runner test
```

## Architecture

See [spec/ARCHITECTURE.md](spec/ARCHITECTURE.md) for the full system architecture and links to ADRs.

Key separation: IAMQ is the inter-agent backbone. Telegram is the human notification layer. Never substitute one for the other.

## Extending

- Add IAMQ operations: edit `tools/iamq_bindings/lib/iamq_bindings.ex`
- Add pipeline stages: edit `tools/pipeline_runner/pipeline_runner/main.py`
- Record architecture decisions: `docker compose run arch-cli new "Title"`
- All new tools must be containerized (see ADR-003)
