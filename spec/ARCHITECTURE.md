# Architecture

## Overview

The Openclaw Main Agent is the orchestrator present in every Openclaw installation. It monitors all other agents via IAMQ, dispatches information to the user, and documents inter-agent interactions. It performs no direct actions on external systems.

## Components

```
┌─────────────────────────────────────────────────────┐
│                   Main Agent                         │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │ Elixir IAMQ  │  │  Heartbeat   │  │ Telegram  │  │
│  │  Bindings    │  │    Loop      │  │  Bridge   │  │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  │
│         │                 │                │         │
└─────────┼─────────────────┼────────────────┼─────────┘
          │                 │                │
          ▼                 ▼                ▼
   ┌──────────┐    ┌──────────────┐   ┌──────────┐
   │   IAMQ   │    │  Workspace   │   │ Telegram │
   │  Server  │    │  Filesystem  │   │   API    │
   └──────────┘    └──────────────┘   └──────────┘
```

### Elixir IAMQ Bindings

HTTP client for the Inter-Agent Message Queue. Handles registration, heartbeats, message sending/receiving, and agent discovery. See [ADR-001](./../.archgate/adrs/001-elixir-for-iamq-bindings.md) for the Elixir choice rationale.

Run: `docker compose run iamq_bindings mix test`

### Heartbeat Loop

Recurring cycle that polls the inbox, scans the workspace for health signals, processes and routes messages, and reports anomalies. Defined in HEARTBEAT.md at the project root.

### Telegram Bridge

User-facing notification layer. Sends anomaly reports, status summaries, and escalation alerts. Never used for agent-to-agent communication — that's IAMQ's job.

### Pipeline Runner

Python-based CI/CD orchestration module. Runs lint, test, build, and deploy stages inside containers. See [ADR-002](./../.archgate/adrs/002-python-poetry-pipeline-runner.md) for the Python + Poetry choice.

Run: `docker compose run pipeline_runner poetry run pytest`

### arch-cli

Architecture documentation tool. Manages ADRs in `.archgate/adrs/`. See [ADR-003](./../.archgate/adrs/003-zero-install-containerization.md) for the containerization strategy.

Run: `docker compose run arch-cli <command>`

## Communication Layers

| Layer    | Purpose                  | Protocol | Audience |
|----------|--------------------------|----------|----------|
| IAMQ     | Agent-to-agent backbone  | HTTP/WS  | Agents   |
| Telegram | User-facing notifications| HTTPS    | Human    |

These layers are strictly separated. IAMQ messages never go to Telegram. Telegram notifications never route through IAMQ.

## Architecture Decisions

All architectural decisions are recorded as ADRs in `.archgate/adrs/`:

- [ADR-001: Elixir for IAMQ Bindings](./../.archgate/adrs/001-elixir-for-iamq-bindings.md) — OTP reliability for message queue integration
- [ADR-002: Python + Poetry for Pipeline Runner](./../.archgate/adrs/002-python-poetry-pipeline-runner.md) — Familiar automation language with reproducible deps
- [ADR-003: Zero-Install Containerization](./../.archgate/adrs/003-zero-install-containerization.md) — Every tool runs in a container, host needs only Docker/Podman
