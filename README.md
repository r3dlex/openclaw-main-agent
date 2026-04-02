<p align="center">
  <img src="assets/banner.svg" alt="openclaw-main-agent" width="600">
</p>

# Openclaw Main Agent

The orchestrator agent present in every [Openclaw](https://docs.openclaw.ai/) installation. Monitors all other agents via the Inter-Agent Message Queue (IAMQ), dispatches information to the user, and documents inter-agent interactions.

This agent observes, routes, and reports. It performs no direct actions on external systems.

## Prerequisites

- Docker or Podman. Nothing else.

## Setup

```bash
git clone <repo-url>
cd openclaw-main-agent
cp .env.example .env
# Edit .env with your values
docker compose build
docker compose up
```

## Commands

All commands run inside containers. No local tool installations required.

```bash
# Run Elixir IAMQ binding tests
docker compose run iamq_bindings mix test

# Run Python pipeline runner tests
docker compose run pipeline_runner poetry run pytest

# Run a pipeline stage
docker compose run pipeline_runner poetry run pipeline-runner test

# Manage Architecture Decision Records
docker compose run arch-cli new "Decision Title"
docker compose run arch-cli list
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENCLAW_AGENTS_WORKSPACE_DIR` | Path to agents workspace | — |
| `IAMQ_BASE_URL` | IAMQ server base URL (see [openclaw-inter-agent-message-queue](https://github.com/r3dlex/openclaw-inter-agent-message-queue)) | `http://127.0.0.1:18790` |
| `AGENT_ID` | Agent identifier | `main` |
| *(Telegram)* | Managed by OpenClaw gateway (`~/.openclaw/openclaw.json`) | — |

## Architecture

The main agent has three communication layers:

- **IAMQ** (Elixir bindings) — agent-to-agent message backbone
- **Telegram** — user-facing notifications
- **Filesystem** — workspace health monitoring

For details, see [spec/ARCHITECTURE.md](spec/ARCHITECTURE.md).

## Project Structure

- `IDENTITY.md`, `SOUL.md`, `BOOT.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `TOOLS.md` — Openclaw template files
- `AGENTS.md` — Agent self-reference (progressive disclosure)
- `spec/` — Developer reference documentation
- `tools/` — Containerized tooling (Elixir, Python, arch-cli)
- `.archgate/adrs/` — Architecture Decision Records
- `.github/workflows/` — CI/CD pipelines

## Links

### Core Infrastructure
- [openclaw-inter-agent-message-queue](https://github.com/r3dlex/openclaw-inter-agent-message-queue) — Inter-Agent Message Queue (IAMQ): HTTP + WebSocket message bus, agent registry, cron scheduler

### Agents
| Agent | Repo | Purpose |
|---|---|---|
| `claude_agent` | [openclaw-agent-claude](https://github.com/r3dlex/openclaw-agent-claude) | Claude AI orchestrator |
| `tempo_agent` | [openclaw-ai-tempo-agent](https://github.com/r3dlex/openclaw-ai-tempo-agent) | AI usage analytics |
| `gitrepo_agent` | [openclaw-gitrepo-agent](https://github.com/r3dlex/openclaw-gitrepo-agent) | Git repo monitoring |
| `health_agent` | [openclaw-health-fitness](https://github.com/r3dlex/openclaw-health-fitness) | Health & fitness tracking |
| `instagram_agent` | [openclaw-instagram-agent](https://github.com/r3dlex/openclaw-instagram-agent) | Instagram engagement |
| `journalist_agent` | [openclaw-journalist-agent](https://github.com/r3dlex/openclaw-journalist-agent) | News briefings |
| `librarian_agent` | [openclaw-librarian-agent](https://github.com/r3dlex/openclaw-librarian-agent) | Document indexing (Obsidian) |
| `mail_agent` | [openclaw-mail-agent](https://github.com/r3dlex/openclaw-mail-agent) | Email management |
| `podcast_agent` | [openclaw-podcast-agent](https://github.com/r3dlex/openclaw-podcast-agent) | Podcast production |
| `sysadmin_agent` | [openclaw-sysadmin-agent](https://github.com/r3dlex/openclaw-sysadmin-agent) | System administration |
| `workday_agent` | [openclaw-workday-agent](https://github.com/r3dlex/openclaw-workday-agent) | Workday HR automation |

### Documentation
- [Openclaw Documentation](https://docs.openclaw.ai/)
