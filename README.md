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
| `IAMQ_BASE_URL` | IAMQ server URL | `http://127.0.0.1:18790` |
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

- [Openclaw Documentation](https://docs.openclaw.ai/)
- [IAMQ Protocol](https://github.com/openclaw/openclaw-inter-agent-message-queue)
