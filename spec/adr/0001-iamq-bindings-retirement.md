# 0001. Retire `tools/iamq_bindings/`

Date: 2026-06-05

## Status

Accepted

## Context

`openclaw-main-agent` historically shipped **two** Elixir IAMQ client
libraries:

1. **`iamq/`** — a GenServer-based sidecar using `IamqSidecar.MqClient`
   and `IamqSidecar.MqWsClient`. The canonical sidecar, also vendored in
   `openclaw-inter-agent-message-queue/sidecar/`.
2. **`tools/iamq_bindings/`** — a pure-function Elixir HTTP wrapper
   around the IAMQ REST API (`IamqBindings.register/5`, `send_message/4`,
   `poll_inbox/2`, etc.). Built as a Docker service (`iamq_bindings:`)
   with its own `mix.exs` and `mix.lock`.

The Wave 0.PR2 extraction (see
`ralplan-openclaw-modernization-001` §4.1) moved the canonical
`IamqSidecar.MqClient` / `MqWsClient` into
`openclaw-shared-base/iamq_sidecar` as a path-dep that every Elixir
agent now imports. The `tools/iamq_bindings/` library was a parallel
implementation that:

- Duplicated the same operations already provided by
  `IamqSidecar.MqClient`.
- Was never imported by any other agent (a `grep` shows zero
  `alias IamqBindings` references in the rest of the OpenClaw
  workspace).
- Carried its own `mix.exs` pinned to Elixir `~> 1.15`, blocking the
  Wave 2 fleet-wide 1.18 bump for the main-agent repo.
- Lacked the shared sidecar's GenServer-based heartbeats, retry
  semantics, and WebSocket push — i.e. it was strictly less capable
  than the alternative it shadowed.

The `iam/` directory referenced in the plan as a third orphan does
**not** exist in this repo (it was already removed in an earlier
commit). Only `tools/iamq_bindings/` requires deletion.

## Decision

Delete `tools/iamq_bindings/` and update every reference to point at
the shared sidecar.

The `iamq/` directory (GenServer sidecar) is **retained** in this PR.
Migrating `iamq/` from a local Docker build context to a
`docker-compose` service that builds from `openclaw-shared-base` is a
larger refactor (requires a shared-base Docker image tag and a compose
override) tracked as a follow-up. The current PR scope per
`ralplan-openclaw-modernization-001` §4.3 M6 is the orphan retirement
only.

## Consequences

- **Easier**: one IAMQ client per agent, with consistent semantics
  (registration, heartbeat, inbox, send, broadcast, ack).
- **Easier**: `iamq_bindings` no longer pins Elixir `~> 1.15`, so the
  repo is unblocked for the fleet-wide 1.18 bump.
- **Easier**: removing the `iamq_bindings` Docker service, CI matrix
  entry, docs job, and lint step shrinks CI wall time and surface
  area.
- **Harder**: a future maintainer who runs `docker compose run
  iamq_bindings mix test` will get a "no such service" error. This
  is documented in the spec/ updates.
- **Harder**: any code that *did* import `IamqBindings` would break
  at compile time. Verified by `grep -r 'IamqBindings' --include='*.ex'
  --include='*.exs' .` → 0 matches in this repo. (The skill doc
  `.claude/skills/openclaw-env.md` is updated to use
  `IamqSidecar.MqClient` instead.)

## Alternatives considered

- **Keep `iamq_bindings` for backwards compatibility** (option a):
  rejected. The library is unused outside the repo; "backwards
  compatibility" has no consumer to protect.
- **Move `iamq_bindings` into `openclaw-shared-base`** (option c):
  rejected. The shared sidecar already provides the same surface
  area with stronger semantics. Adding a second IAMQ client to the
  shared package would dilute the canonical API.
- **In-place git init + submodule** (option d): rejected. Adds
  friction and breaks the `make ci` flow.
