# CI/CD Pipelines

All pipeline stages execute inside containers, both locally and in CI.

## GitHub Actions Workflows

Workflows live in `.github/workflows/`:

### lint.yml

Builds container images and runs linting checks.
- Triggers: push to main, pull requests
- Steps: build containers, run linters inside containers

### test.yml

Runs all test suites inside containers.
- Triggers: push to main, pull requests
- Elixir tests: `docker compose run iamq_bindings mix test`
- Python tests: `docker compose run pipeline_runner poetry run pytest`

### build.yml

Builds all container images to verify they compile and install correctly.
- Triggers: push to main, pull requests
- Builds: iamq_bindings, pipeline_runner, arch-cli

## Pipeline Runner

The `pipeline_runner` Python tool orchestrates CI/CD stages:

```bash
# Run all stages
docker compose run pipeline_runner poetry run pipeline-runner run-all

# Run individual stages
docker compose run pipeline_runner poetry run pipeline-runner lint
docker compose run pipeline_runner poetry run pipeline-runner test
docker compose run pipeline_runner poetry run pipeline-runner build
docker compose run pipeline_runner poetry run pipeline-runner deploy
```

## Local Development

Run the same pipeline locally that CI runs:

```bash
# Build all containers
docker compose build

# Run tests
docker compose run iamq_bindings mix test
docker compose run pipeline_runner poetry run pytest
```

## Secrets

All secrets come from GitHub Secrets in CI, never from the repository. Locally, secrets are in `.env` (excluded from git).
