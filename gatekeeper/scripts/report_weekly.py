import json
import os
import glob
from datetime import datetime, timedelta

REPORT_DIR = "REDACTED_PATH/.openclaw/workspace/gatekeeper/knowledge/reports"
DAILY_PATH = os.path.join(REPORT_DIR, "daily")
WEEKLY_PATH = os.path.join(REPORT_DIR, "weekly")

def report_weekly():
    if not os.path.exists(WEEKLY_PATH):
        os.makedirs(WEEKLY_PATH)
        
    # Aggregate last 7 days
    total_prs = 0
    total_jira = set()
    contributors = {}
    
    # Simple logic: Read all .json in daily dir modified in last 7 days? 
    # Better: Calculate filenames for last 7 days.
    
    today = datetime.now()
    summary = {"week_ending": today.strftime("%Y-%m-%d"), "total_prs": 0, "tickets_impacted": 0, "top_contributor": "N/A"}
    
    for i in range(7):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        file = os.path.join(DAILY_PATH, f"{day_str}.json")
        if os.path.exists(file):
            with open(file, "r") as f:
                try:
                    data = json.load(f)
                    total_prs += data.get("count", 0)
                    total_jira.update(data.get("jira_tickets", []))
                    
                    for user, count in data.get("contributors", {}).items():
                        contributors[user] = contributors.get(user, 0) + count
                except:
                    pass

    summary["total_prs"] = total_prs
    summary["tickets_impacted"] = len(total_jira)
    
    if contributors:
        top_user = max(contributors, key=contributors.get)
        summary["top_contributor"] = f"{top_user} ({contributors[top_user]} PRs)"
        summary["all_contributors"] = contributors

    # Save
    with open(f"{WEEKLY_PATH}/week_{today.strftime('%Y_W%U')}.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    report_weekly()
