from ado_client import get_data
import sys
import json

def evaluate(pr_id):
    # 1. Get PR Details
    pr = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
    if not pr:
        return {"id": pr_id, "score": 0, "reason": "Not Found"}
        
    # 2. Get Changes (Commits/Files)
    # Using 'iterations' or 'commits' to estimate size
    commits = get_data(f"git/repositories/{pr['repository']['id']}/pullRequests/{pr_id}/commits", {"api-version": "7.0"})
    num_commits = len(commits.get("value", []))
    
    # Get thread status (comments)
    threads = get_data(f"git/repositories/{pr['repository']['id']}/pullRequests/{pr_id}/threads", {"api-version": "7.0"})
    active_comments = sum(1 for t in threads.get("value", []) if t.get("status") in ["active", "pending"])
    
    # 3. Scoring Logic
    score = 10
    reason = []
    
    # Penalty: No description
    if not pr.get("description"):
        score -= 2
        reason.append("No description")
        
    # Penalty: Active comments
    if active_comments > 0:
        score -= 3
        reason.append(f"{active_comments} active comments")
        
    # Penalty: Too many commits (might be messy)
    if num_commits > 5:
        score -= 1
        reason.append("Many commits (>5)")
        
    # Heuristic: Title keywords
    title = pr["title"].lower()
    if "fix" in title or "bug" in title:
        pass # Good
    elif "refactor" in title:
        score -= 1 # Riskier in freeze
        reason.append("Refactoring in freeze")
    elif "security" in title or "cve" in title:
        score += 1 # Priority boost (cap at 10)
        
    # Author Trust (Mockup - usually we'd check history)
    # Assuming Florian/Hauk/Juily are trusted seniors/regulars.
    
    return {
        "id": pr_id,
        "title": pr["title"],
        "author": pr["createdBy"]["displayName"],
        "score": min(10, score),
        "reasons": reason,
        "repo": pr["repository"]["name"],
        "url": pr["url"]
    }

if __name__ == "__main__":
    ids = sys.argv[1:]
    results = [evaluate(pid) for pid in ids]
    print(json.dumps(results, indent=2))
