from ado_client import get_data
from datetime import datetime, timedelta
import re, json, os

# Hardcoded path matching directory creation
REPORT_DIR = "REDACTED_PATH/.openclaw/workspace/gatekeeper/knowledge/reports"
REPORT_PATH = os.path.join(REPORT_DIR, "daily")

def report():
    if not os.path.exists(REPORT_PATH):
        os.makedirs(REPORT_PATH)

    yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
    data = get_data("git/pullrequests", {
        "searchCriteria.status": "completed",
        "searchCriteria.minTime": yesterday,
        "api-version": "7.0"
    })

    stats = {"count": 0, "jira_tickets": [], "contributors": {}}
    
    for pr in data.get("value", []):
        stats["count"] += 1
        # Find DEV-####
        text = (pr.get("title", "") or "") + (pr.get("description", "") or "")
        stats["jira_tickets"].extend(re.findall(r"DEV-\d+", text))
        # Count Author
        auth = pr["createdBy"]["displayName"]
        stats["contributors"][auth] = stats["contributors"].get(auth, 0) + 1

    # Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"{REPORT_PATH}/{date_str}.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    report()
