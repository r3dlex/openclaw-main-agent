# Wave 2 Modernization Log — openclaw-main-agent

Tracking issue: #7

This log records the three sub-PRs that delivered the Wave 2.EX.B
modernization scope for `openclaw-main-agent` per
`ralplan-openclaw-modernization-001` §4.3 M6.

## Sub-PRs

| # | Title | PR | Status |
|---|-------|----|--------|
| 1 | `refactor(main-agent): retire tools/iamq_bindings/ orphan (AC-E18)` | #8 | MERGED |
| 2 | `chore(main-agent): tooling + coverage gate (sub-PR 2)` | #9 | OPEN — awaiting manual review |
| 3 | `docs(main-agent): Wave 2 modernization log (sub-PR 3)` | this PR | OPEN — awaiting manual review |

## Acceptance criteria status (12/12)

| AC | Description | Sub-PR | Status |
|----|-------------|--------|--------|
| AC-E18 | Delete orphan `tools/iamq_bindings/` library | 1 | DONE |
| AC-P11 | Python package rename (`tools/pipeline_runner` → preserved as Python package) | n/a | N/A (Python source untouched) |
| AC-U7 | Fleet-wide Elixir 1.18 bump for `iamq/` | 1 + 2 | DONE (mix.exs now `~> 1.18`) |
| AC-U9 | Sub-PR cadence (1 auto, 2 + 3 manual review) | 1, 2, 3 | DONE |
| AC-M1 | Green-base build verified on host Elixir 1.19.5 | 2 | DONE |
| AC-M2 | `mix format --check-formatted` clean | 2 | DONE |
| AC-M3 | `mix compile --warnings-as-errors` clean | 2 | DONE |
| AC-M4 | `mix credo --strict` runs (3 pre-existing refactor ops, non-fatal) | 2 | DONE |
| AC-M5 | Makefile `ci` target emits JSON sentinel | 2 | DONE |
| AC-M6 | `.github/workflows/ci.yml` `make-ci` job present | 2 | DONE |
| AC-T1 | Coverage gate `excoveralls` threshold ≥90% | 2 | CONFIGURED (no tests in repo — see Notes) |
| AC-T2 | Tracking issue closure | 3 | DONE (this PR closes #7) |

## R4 risk mitigation (green-base on host Elixir 1.19.5)

Verified on 2026-06-05 with the local `elixir 1.19.5` toolchain:

- `mix compile --warnings-as-errors` → exit 0
- `mix format --check-formatted` → exit 0
- `mix credo --strict` → 3 pre-existing refactor ops in
  `gateway_client.ex` (cyclomatic complexity 12 in `format_message/1`,
  two pipe-chain-start in `generate_and_persist_identity`). Pre-PR
  state — not introduced by this modernization.

## Notes

### Why no `mix test` coverage runs

`openclaw-main-agent` is a **host-native** agent: its primary
runtime is the Docker Compose service defined at the repo root, and
`iamq/` is a vendored sidecar library (GenServer + WebSockex) that
is exercised by its consumer agents (mail, sysadmin, etc.) on
their test suites — not by this repo. The mix.exs test_coverage
threshold is set to 90% (per AC-T1) as a forward-looking gate for
when a test suite is added to `iamq/` directly; the Makefile's
`mix-cover` target and the `excoveralls` dependency are wired and
will produce an HTML report under `iamq/cover/` once a `test/`
directory exists.

### Out-of-scope items (not blocking this PR)

- **Refactoring `gateway_client.ex` refactor opportunities** —
  flagged during `mix credo --strict` review. Cyclomatic
  complexity 12 in `format_message/1` is driven by the nested
  try/rescue + if/else + case ladder for handling
  `gitrepo deliver_report` actions. Best fixed by extracting a
  `format_deliver_report/1` helper, but it changes the message
  formatting behavior and is not load-bearing for the
  modernization goals. Tracking as a follow-up.

- **Migrating `iamq/` Docker build to consume `openclaw-shared-base`
  as a published dep** — the `iamq/` Docker build context still
  vendors the sidecar from this repo. Wave 0.PR2 already extracted
  the canonical sidecar into `openclaw-shared-base/iamq_sidecar/`;
  the per-agent Dockerfile update + image-tag coordination is a
  larger refactor, explicitly out of scope per ADR 0001.

- **CI matrix expansion** — `test.yml` and `lint.yml` still target
  the `pipeline_runner` Python service (the only existing Docker
  service with a test/lint cycle). When the `iamq/` build context
  migrates to `openclaw-shared-base`, the matrix should add an
  `iamq` entry mirroring the existing `pipeline_runner` pattern.

## Cross-references

- Plan: `ralplan-openclaw-modernization-001` §4.3 M6
- ADR: `spec/adr/0001-iamq-bindings-retirement.md`
- Sub-PR 1 commit: `28e8e77` (via PR #8)
- Sub-PR 2 commit: `f746b39` (via PR #9)
- Sub-PR 3 commit: (this PR)

Closes #7.
