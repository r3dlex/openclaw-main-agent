# Troubleshooting

Known failure modes and their fixes. Follow the decision tree: symptom → cause → fix.

## IAMQ Connectivity

**Symptom:** `POST /register` returns connection refused.
- **Cause:** IAMQ server not running.
- **Fix:** Start the IAMQ service. Verify `$IAMQ_BASE_URL` is correct. Check that port 18790 is not blocked.

**Symptom:** `GET /inbox/main` returns 404.
- **Cause:** Agent not registered with IAMQ.
- **Fix:** Re-run the registration step from BOOT.md.

**Symptom:** Messages sent but never received by target agent.
- **Cause:** Target agent not polling its inbox, or agent_id mismatch.
- **Fix:** Verify target agent is registered (`GET /agents`). Check the `to` field matches the target's `agent_id`.

## Telegram Delivery

**Symptom:** Notifications not arriving in Telegram.
- **Cause:** Invalid bot token or chat ID.
- **Fix:** Verify `$TELEGRAM_BOT_TOKEN` and `$TELEGRAM_CHAT_ID` in `.env`. Test with a manual curl to the Telegram API.

**Symptom:** Telegram rate limiting (429 errors).
- **Cause:** Too many messages sent in a short period.
- **Fix:** Batch notifications. The heartbeat loop should aggregate findings before sending a single Telegram message.

## Stale Heartbeats

**Symptom:** Agent appears in registry but hasn't sent a heartbeat in >30 minutes.
- **Cause:** Agent crashed, stuck, or disconnected.
- **Fix:** Check the agent's workspace for error logs. Restart the agent if needed. Report via Telegram.

## Container Issues

**Symptom:** `docker compose run` fails with build errors.
- **Cause:** Dependency resolution failure or Dockerfile issue.
- **Fix:** Run `docker compose build --no-cache <service>` to rebuild from scratch. Check Dockerfile for pinned version conflicts.

**Symptom:** Tests pass locally but fail in CI.
- **Cause:** Environment variable differences between local `.env` and GitHub Secrets.
- **Fix:** Compare `.env.example` with CI workflow env configuration. Ensure all required vars are set in GitHub Secrets.
