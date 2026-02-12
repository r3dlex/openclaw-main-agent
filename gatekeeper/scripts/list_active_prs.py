from ado_client import get_data
import json

def list_active_prs():
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-requests?view=azure-devops-rest-7.0
    # status=active is default, but good to specify.
    prs = get_data("git/pullrequests", {"searchCriteria.status": "active", "api-version": "7.0"})
    
    if not prs:
        print("No active PRs found or error.")
        return

    active_prs = prs.get("value", [])
    print(f"Found {len(active_prs)} active PRs.")
    
    for pr in active_prs:
        print(f"PR #{pr['pullRequestId']}: {pr['title']} ({pr['createdBy']['displayName']})")

if __name__ == "__main__":
    list_active_prs()
