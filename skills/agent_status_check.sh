#!/bin/bash
# agent_status_check - Check status of all registered agents via IAMQ
INPUT=$(cat)
IAMQ_URL="${IAMQ_HTTP_URL:-http://host.docker.internal:18790}"
RESPONSE=$(curl -sf "$IAMQ_URL/registry" 2>&1 || echo "{}")
echo "{\"result\": \"ok\", \"skill\": \"agent_status_check\", \"registry\": $RESPONSE}"
