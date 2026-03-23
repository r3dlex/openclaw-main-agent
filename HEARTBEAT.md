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

5. **Report to user** — send a summary to the user via Telegram after EVERY heartbeat cycle, not just when anomalies are found:
   - Telegram is the human visibility layer — the user CANNOT see IAMQ messages
   - IAMQ is the inter-agent backbone — never substitute one for the other
   - If notable events occurred: summarize agent activity, anomalies, and status changes.
     Example: "Heartbeat: 8/9 agents online. Mail Agent filed 12 emails. Journalist published briefing. GitRepo evaluated 2 PRs."
   - If nothing happened: a brief "All agents online and healthy. No notable events." is fine.
   - Errors, agent crashes, stale heartbeats: report IMMEDIATELY, don't wait for the cycle to finish.

6. **Stay concise** — the user wants to know what's happening, not get spammed. One summary per cycle is ideal. Only skip reporting entirely if truly nothing happened AND the last report was recent (within the hour).
