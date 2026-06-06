# Supply-Chain Pins

> Tracks the pinned digests of base Docker images that `openclaw-main-agent`
> builds against. The pin is to a content-addressable digest, not a floating
> tag, so the build is reproducible and immune to upstream image re-pushes
> or silent rebuilds.

## Current Pins

| Component | Version label | Digest | Source |
|---|---|---|---|
| `elixir:1.18-slim` | elixir 1.18 | `sha256:d6af827ff3a37d03572c8b4fe5dee64548e63194bb2bd851f015525e8361f9c8` | `docker pull elixir:1.18-slim` + `docker images --digests elixir:1.18-slim` |
| `python:3.12-slim` | Python 3.12 | `sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203` | `docker pull python:3.12-slim` + `docker images --digests python:3.12-slim` |

> The version label is human-readable; the digest is the integrity guarantee.
> The digest in the `Dockerfile` and the value recorded here must always match.

## Where the Pins Live in the Code

| File | Line(s) | What it pins |
|---|---|---|
| `iamq/Dockerfile` | line 1 `FROM` | `elixir:1.18-slim` digest (build stage) |
| `iamq/Dockerfile` | line 10 `FROM` | `elixir:1.18-slim` digest (runtime stage) |
| `tools/pipeline_runner/Dockerfile` | line 1 `FROM` | `python:3.12-slim` digest |

Both `FROM` lines in `iamq/Dockerfile` carry the same digest — the build
stage and the runtime stage are pinned to the exact same upstream image
so the artifacts are reproducible bit-for-bit.

## Bump Procedure

Follow these steps exactly when bumping either pin. The bump is a normal
PR; it does **not** rewrite history of `main` and does **not** force-push.

### A. Bump `elixir:1.18-slim`

1. On a workstation with Docker installed, discover the new digest:
   ```bash
   docker pull elixir:1.18-slim
   docker images --digests elixir:1.18-slim
   ```
2. Update both `FROM` lines in `iamq/Dockerfile` with the new digest.
3. Update the `elixir:1.18-slim` row of the **Current Pins** table.
4. Add a row to the **History** table.
5. Open a PR titled `chore(supply-chain): bump elixir:1.18-slim digest`.

### B. Bump `python:3.12-slim`

1. Discover the new digest:
   ```bash
   docker pull python:3.12-slim
   docker images --digests python:3.12-slim
   ```
2. Update the `FROM` line in `tools/pipeline_runner/Dockerfile`.
3. Update the `python:3.12-slim` row of the **Current Pins** table.
4. Add a row to the **History** table.
5. Open a PR titled `chore(supply-chain): bump python:3.12-slim digest`.

### C. Pre-Merge Checklist

- [ ] `docker build -t main-agent-iamq:pin-test iamq/` succeeds locally.
- [ ] `docker build -t main-agent-pipeline-runner:pin-test tools/pipeline_runner/` succeeds locally.
- [ ] `spec/SUPPLY_CHAIN.md` is updated and committed in the **same** PR.
- [ ] PR description includes the old digest, the new digest, and the rationale.

## Out of Scope (for this file)

- `openclaw-shared-base` SHA pin (consumed via `iamq_sidecar` path-dep
  in `iamq/mix.exs`; pinned separately in the fleet-wide shared-base bump
  wave — see `openclaw-gitrepo-agent/spec/SUPPLY_CHAIN.md` for the
  authoritative cross-repo table).
- The `curl -fsSL https://deb.nodesource.com/setup_22.x | bash` step in
  `iamq/Dockerfile` (nodejs install via nodesource script). A separate
  concern; would benefit from a nodejs image hash pin in a follow-up PR.
- The `alpine/git` digest pin (not consumed by this repo).
- The `elixir:1.17-otp-27-slim` (in `factory/Dockerfile` of
  `openclaw-agent-claude`) vs `elixir:1.18` (here) version mismatch — a
  fleet-wide modernization concern, tracked separately.

## History

| Date | Component | Old pin | New pin | PR |
|---|---|---|---|---|
| 2026-06-06 | `elixir:1.18-slim` | floating tag (`elixir:1.18-slim`) | `sha256:d6af827ff3a37d03572c8b4fe5dee64548e63194bb2bd851f015525e8361f9c8` | (initial pin PR) |
| 2026-06-06 | `python:3.12-slim` | floating tag (`python:3.12-slim`) | `sha256:090ba77e2958f6af52a5341f788b50b032dd4ca28377d2893dcf1ecbdfdfe203` | (initial pin PR) |
