from ado_client import BASE_URL, get_headers
import requests
import sys
import json
import os

# Need to know MY id to vote.
# Usually we PUT to .../reviewers/{reviewerId}
# Or we can just create a thread? No, vote is specific.
# Easier way: Just create a script that uses requests directly if we know the endpoint.
# Endpoint: PATCH https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repositoryId}/pullRequests/{pullRequestId}/reviewers/{reviewerId}?api-version=7.0

# But we need to know OUR reviewer ID.
# Alternative: Browser Relay is safer if we don't know our own descriptor ID easily via API without a lookup.

# Let's try to lookup "me" first.
def get_me():
    url = "https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version=7.1-preview.1"
    # This might require different scope/endpoint.
    # ADO "core" get authorized user:
    # https://dev.azure.com/{org}/_apis/connectionData
    
    # Actually, simpler:
    # I'll stick to Browser Relay for the Approval action to be 100% sure I'm acting as "Andre" visually.
    # Writing a robust API voter in 1 min is risky if the PAT scope is "Code (Read)" only.
    pass

# ABORT API STRATEGY. Switching to Browser Relay for Approval action.
