# HEARTBEAT.md - Recurring Loop

Execute this loop on each heartbeat cycle:

1. **Send heartbeat** to IAMQ:
   ```
   POST $IAMQ_BASE_URL/heartbeat
   { "agent_id": "main" }
   ```

2. **Poll inbox** for unread messages:
   ```
   GET $IAMQ_BASE_URL/inbox/main?status=unread
   ```

3. **Process messages** — for each message:
   - Route to the appropriate handler based on message type and subject
   - Reply via `POST $IAMQ_BASE_URL/send` with `replyTo` set to the original message ID
   - Mark handled: `PATCH $IAMQ_BASE_URL/messages/:id` with `{"status": "acted"}`

4. **Scan workspace** — check `$OPENCLAW_AGENTS_WORKSPACE_DIR` for agent health signals:
   - Stale heartbeats (agent hasn't checked in)
   - Error logs or crash dumps
   - Unusual file activity patterns

5. **Report to user** — if anomalies or notable events are found, notify via Telegram:
   - Telegram is the human visibility layer
   - IAMQ is the inter-agent backbone
   - Never substitute one for the other

6. **Stay quiet** if nothing needs attention. No heartbeat noise to Telegram.
