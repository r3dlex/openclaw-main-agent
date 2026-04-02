# Cron Schedules — openclaw-main-agent

## Overview

The Main agent coordinates cross-agent workflows on schedule. Rather than
running its own data pipelines, it sends IAMQ trigger messages to peer agents
at the appropriate times. This ensures the swarm is orchestrated by a single
authoritative source.

## Schedules

### morning_kickoff
- **Expression**: `0 6 * * 1-5` (06:00 UTC Mon-Fri)
- **Purpose**: Initiate the morning routine across the swarm: instruct Mail to
  tidy the inbox, Journalist to run the morning briefing, and log the results.
  Sends summary to user via Telegram when all sub-tasks complete.
- **Trigger**: Delivered via IAMQ message `cron::morning_kickoff`
- **Handler**: Pipeline `morning_kickoff` in `tools/pipeline_runner/`
- **Expected duration**: 10–20 minutes (waits for peer agents to respond)
- **On failure**: Log which sub-tasks failed; send partial summary to user;
  do not retry individual sub-tasks

### swarm_health_check
- **Expression**: `*/15 * * * *` (every 15 minutes)
- **Purpose**: Poll IAMQ agent registry to detect offline agents. If an agent
  has missed 3+ heartbeats, send an alert to `agent_claude` and the user.
- **Trigger**: Delivered via IAMQ message `cron::swarm_health_check`
- **Handler**: `tools/pipeline_runner/pipelines/health_check.py`
- **Expected duration**: Under 5 seconds
- **On failure**: Log locally; skip alert (cannot send IAMQ if IAMQ is down)

### weekly_summary
- **Expression**: `0 9 * * 1` (09:00 UTC Monday)
- **Purpose**: Collect status reports from all peer agents (GitRepo weekly digest,
  Tempo weekly report, Health Fitness weekly report). Compile into a single
  cross-agent weekly summary and deliver to user.
- **Trigger**: Delivered via IAMQ message `cron::weekly_summary`
- **Handler**: Pipeline `weekly_summary` in `tools/pipeline_runner/`
- **Expected duration**: 5–10 minutes (sequential IAMQ requests to peers)
- **On failure**: Include partial results with a note about which agents failed

## Cron Registration

Registered with IAMQ on startup via `POST /crons`:

```json
[
  {"subject": "cron::morning_kickoff",    "expression": "0 6 * * 1-5"},
  {"subject": "cron::swarm_health_check", "expression": "*/15 * * * *"},
  {"subject": "cron::weekly_summary",     "expression": "0 9 * * 1"}
]
```

The `cron/` directory in this repo contains the canonical cron definitions
used by the IAMQ registration script.

## Manual Trigger

```bash
# Trigger morning kickoff manually
docker compose run pipeline_runner python -m main_agent.orchestrate morning_kickoff

# Check swarm health now
docker compose run pipeline_runner python -m main_agent.health_check
```

---

**Related:** `spec/API.md`, `spec/COMMUNICATION.md`, `spec/ARCHITECTURE.md`
