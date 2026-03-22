# 2. Use Python + Poetry for Pipeline Runner

## Status

Accepted

## Context

CI/CD pipeline orchestration needs a flexible scripting language. Python is well-suited for automation. Poetry provides reproducible dependency management.

## Decision

Use Python 3.12 with Poetry for the pipeline runner tool.

## Consequences

- Standardized dependency management via Poetry lockfile.
- Familiar language for DevOps tasks.
- Containerized execution ensures consistent environments.
