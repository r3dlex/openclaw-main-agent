# API — openclaw-main-agent

## Overview

The Main agent is the orchestrator for the OpenClaw swarm. It does not expose
an HTTP server to other agents. All inter-agent coordination uses IAMQ. The
agent also controls peer agents by sending them IAMQ requests and monitoring
responses.

---

## IAMQ Message Interface

### Incoming messages accepted by `main`

| Subject | Purpose | Body fields |
|---------|---------|-------------|
| `main.status` | Return swarm health: which agents are online, last heartbeat per agent | — |
| `main.orchestrate` | Trigger a cross-agent workflow | `workflow: string`, `params?: object` |
| `main.broadcast` | Send a message to all registered agents | `subject: string`, `body: string` |
| `main.pipeline` | Run a named pipeline | `name: string`, `args?: object` |
| `main.agent_status` | Query status of a specific peer agent | `agent_id: string` |
| `status` | Return main agent health | — |

#### Example: trigger a cross-agent workflow

```json
{
  "from": "agent_claude",
  "to": "main",
  "type": "request",
  "priority": "NORMAL",
  "subject": "main.orchestrate",
  "body": {
    "workflow": "morning_briefing",
    "params": {"notify_user": true}
  }
}
```

#### Example: swarm status response

```json
{
  "from": "main",
  "to": "agent_claude",
  "type": "response",
  "subject": "main.status.result",
  "body": {
    "online_agents": ["agent_claude", "journalist_agent", "librarian_agent", "mail_agent"],
    "offline_agents": ["tempo_agent"],
    "last_seen": {
      "journalist_agent": "2026-04-02T08:01:00Z",
      "librarian_agent": "2026-04-02T07:55:00Z"
    }
  }
}
```

---

## Outbound Orchestration

The Main agent sends messages to all peer agents. It does not receive data
pipelines from them — it issues commands and monitors acknowledgements.

### Known outbound message subjects

| Target | Subject | Purpose |
|--------|---------|---------|
| `journalist_agent` | `journalist.briefing` | Trigger morning briefing |
| `mail_agent` | `mail.tidy` | Trigger inbox tidy |
| `librarian_agent` | `librarian.index` | Trigger vault reindex |
| `gitrepo_agent` | `repo.scan` | Trigger repo scan |
| `broadcast` | `main.broadcast` | Swarm-wide announcements |

---

## IAMQ Bindings (Elixir)

The `tools/iamq_bindings/` Elixir library is the core messaging client used by
this agent. It wraps IAMQ HTTP calls and provides typed message structs.
Other agents in the swarm that use Elixir import this library.

```bash
# Test the bindings
docker compose run iamq_bindings mix test

# Check swarm status via CLI
docker compose run pipeline_runner python -m main_agent.status
```

---

**Related:** `spec/COMMUNICATION.md`, `spec/ARCHITECTURE.md`, `spec/PIPELINES.md`
