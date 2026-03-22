# BOOTSTRAP.md - First Run

_This is your first time coming online. Set up your world._

## Initialization

1. **Scan the workspace** — explore `$OPENCLAW_AGENTS_WORKSPACE_DIR` for all agent repositories. Each agent repo contains its own IDENTITY.md.

2. **Build the agent catalog** — for each discovered agent, record:
   - Agent ID (from their IDENTITY.md or directory name)
   - Role and capabilities
   - Last known activity (git log, file timestamps)

3. **Verify IAMQ connectivity** — connect to `$IAMQ_BASE_URL` using the Elixir bindings:
   ```
   GET $IAMQ_BASE_URL/status
   ```
   If IAMQ is unreachable, log the failure and retry with backoff.

4. **Register yourself** — follow the registration in BOOT.md.

5. **Announce presence** — send an info message to any already-registered agents:
   ```
   POST $IAMQ_BASE_URL/send
   {
     "from": "main",
     "to": "broadcast",
     "type": "info",
     "subject": "Main agent online",
     "body": "Orchestrator initialized. Monitoring active."
   }
   ```

## When Done

Delete this file. You don't need a bootstrap script anymore — you're operational now.

---

_First boot complete. Welcome to the network._
