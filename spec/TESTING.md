# Testing

All tests run inside containers. Nothing on the host.

## Elixir IAMQ Bindings

```bash
docker compose run iamq_bindings mix test
```

Tests cover each IAMQ operation: register, heartbeat, send, poll inbox, mark message, list agents, health check.

## Python Pipeline Runner

```bash
docker compose run pipeline_runner poetry run pytest
```

Tests cover CLI invocation for each pipeline stage (lint, test, build, deploy) and error handling.

With coverage:

```bash
docker compose run pipeline_runner poetry run pytest --cov=pipeline_runner
```

## Integration Testing

Full heartbeat loop integration test:

1. Start IAMQ service
2. Run the main agent boot sequence
3. Verify registration via `GET /agents/main`
4. Send a test message to `main` inbox
5. Trigger a heartbeat cycle
6. Verify the message was processed (status changed to `acted`)

This requires a running IAMQ instance. Use docker compose to bring up all services:

```bash
docker compose up -d
```

## Adding Tests

- Elixir tests go in `tools/iamq_bindings/test/`
- Python tests go in `tools/pipeline_runner/tests/`
- Follow existing patterns: one test file per module, descriptive test names
