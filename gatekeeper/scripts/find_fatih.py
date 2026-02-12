from ado_client import get_data
import json

def find_fatih_prs():
    # Search active PRs created by anyone named "Fatih"
    data = get_data("git/pullrequests", {"searchCriteria.status": "active", "api-version": "7.0"})
    
    found = []
    for pr in data.get("value", []):
        creator = pr["createdBy"]["displayName"]
        title = pr["title"]
        reviewers = [r["displayName"] for r in pr.get("reviewers", [])]
        
        # Check if Fatih is creator OR reviewer
        if "Fatih" in creator or any("Fatih" in r for r in reviewers):
            found.append({
                "id": pr["pullRequestId"],
                "title": title,
                "creator": creator,
                "url": pr["url"]
            })
            
    print(json.dumps(found, indent=2))

if __name__ == "__main__":
    find_fatih_prs()
