from ado_client import get_data
import json

FREEZE_GROUP = "RIB 4.0 Freeze Reviewers"

def audit():
    # Get active PRs
    data = get_data("git/pullrequests", {"searchCriteria.status": "active", "api-version": "7.0"})
    flagged = []

    for pr in data.get("value", []):
        reviewers = pr.get("reviewers", [])
        # Check if Freeze Group is a reviewer
        has_freeze_group = any(FREEZE_GROUP in r["displayName"] for r in reviewers)
        
        if has_freeze_group:
            # Check for non-freeze group approvals (Vote 10=Approved, 5=WithSuggestions)
            team_approved = any(
                r["vote"] > 0 and FREEZE_GROUP not in r["displayName"] 
                for r in reviewers
            )
            
            if not team_approved:
                flagged.append(f"PR {pr['pullRequestId']}: {pr['title']} (Missing Team Vote)")

    print(json.dumps(flagged, indent=2) if flagged else "No violations found.")

if __name__ == "__main__":
    audit()
