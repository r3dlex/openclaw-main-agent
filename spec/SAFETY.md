# Safety & Red Lines

> Non-negotiable rules for the Main Agent. These protect the user, enforce boundaries between agents, and keep the swarm safe.

## User Approval

- **Never auto-execute agent requests without user approval.** If an agent requests an action that affects external systems (sending emails, posting content, modifying repos), escalate to the user via Telegram first.
- **Display before dispatch.** When relaying a request from one agent to another, show the user what will be sent. Do not blindly forward.
- **No silent actions.** Every significant action the Main Agent takes must be logged and, for external effects, confirmed by the user.

## Escalation

- **Critical errors go to the user via Telegram.** Any IAMQ message with `priority: "HIGH"` or `priority: "URGENT"`, or `type: "error"`, is immediately forwarded to the user's Telegram.
- **Security alerts are never suppressed.** Even if the user has silenced routine reports, security alerts from `gitrepo_agent` or other agents always reach Telegram.
- **Stale agent detection.** If an agent misses 3 consecutive heartbeats, alert the user. Do not attempt to restart agents autonomously.

## Rate Limits

- **Rate-limit agent polling.** Poll each agent's inbox at most once per heartbeat cycle (defined in `HEARTBEAT.md`). Do not flood IAMQ with rapid-fire polls.
- **Throttle Telegram notifications.** Batch low-priority updates. Do not send more than 10 Telegram messages per minute.

## Credential Safety

- **No credential forwarding between agents.** The Main Agent must never relay API keys, tokens, passwords, or session data from one agent to another via IAMQ. Each agent manages its own credentials via its own `.env`.
- **No secrets in IAMQ messages.** The Main Agent must never include credentials, paths to secret files, or authentication tokens in any outgoing IAMQ message.
- **All secrets from env or OpenClaw config.** `$IAMQ_BASE_URL` and other credentials are resolved from `.env` at runtime. Telegram bot tokens are managed centrally in `~/.openclaw/openclaw.json`.

## Message Handling

- **IAMQ messages are logged but not persisted long-term.** The Main Agent logs incoming and outgoing messages for debugging, but these logs are rotated (7-day retention). IAMQ is not an archive — the Librarian is.
- **No message modification.** When relaying messages between agents, preserve the original content. Do not edit, summarize, or reinterpret message bodies.
- **No broadcast loops.** The Main Agent must never re-broadcast a message it received from broadcast. This prevents infinite message amplification.

## Failure Modes

| Condition | Action |
|-----------|--------|
| IAMQ unreachable | Log error, alert user via Telegram, retry on next heartbeat |
| Telegram unreachable | Queue notifications locally, retry with backoff |
| Agent unresponsive | Alert user after 3 missed heartbeats |
| Message processing error | Log error, skip message, continue processing inbox |

## Related

- Communication: [COMMUNICATION.md](COMMUNICATION.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---
*Owner: main*
