# 3. Zero-Install Containerization Strategy

## Status

Accepted

## Context

The main agent must run on any host without requiring tool installations. Different components use different languages (Elixir, Python, Node.js).

## Decision

Every tool, test, build step, and CLI runs inside a container. The only host requirement is Docker or Podman.

## Consequences

- Consistent environments across all developer machines and CI.
- No "works on my machine" issues.
- Slightly higher disk usage due to container images.
- All commands use `docker compose run`.
