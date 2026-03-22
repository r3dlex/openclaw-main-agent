# 1. Use Elixir for IAMQ Bindings

## Status

Accepted

## Context

Need reliable HTTP client for inter-agent message queue. IAMQ uses HTTP/WebSocket. Elixir's OTP provides fault tolerance and supervision.

## Decision

Implement IAMQ bindings in Elixir using Req HTTP client and Jason for JSON.

## Consequences

- Requires Elixir runtime (containerized).
- Team must maintain Elixir code.
- Gains OTP reliability and supervision tree benefits.
