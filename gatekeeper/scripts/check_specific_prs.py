from ado_client import get_data
import sys
import json

def check_prs(pr_ids):
    results = []
    for pr_id in pr_ids:
        # Get PR Details
        pr = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
        if not pr or "pullRequestId" not in pr:
            results.append(f"PR {pr_id}: Not Found or Error")
            continue
            
        # Get Threads (Comments) to check for active discussions
        threads = get_data(f"git/repositories/{pr['repository']['id']}/pullRequests/{pr_id}/threads", {"api-version": "7.0"})
        active_comments = sum(1 for t in threads.get("value", []) if t.get("status") in ["active", "pending"])
        
        # Analyze Reviewers
        votes = [r["vote"] for r in pr.get("reviewers", [])]
        approvals = votes.count(10) + votes.count(5)
        rejects = votes.count(-10) + votes.count(-5)
        
        # Determine Status
        status = "✅ OK"
        if rejects > 0: status = "❌ REJECTED"
        elif active_comments > 0: status = "⚠️ COMMENTS OPEN"
        elif approvals == 0: status = "⏳ PENDING APPROVAL"
        
        # Basic "Score" (Mockup logic based on signals)
        score = 10
        if active_comments > 0: score -= 2
        if rejects > 0: score -= 10
        if approvals < 2: score -= 1 # Encourage more eyes
        
        summary = {
            "id": pr_id,
            "title": pr["title"],
            "author": pr["createdBy"]["displayName"],
            "status": status,
            "score": max(0, score),
            "approvals": approvals,
            "active_comments": active_comments,
            "url": pr["url"].replace("_apis/git/repositories", "_git").replace("/pullRequests/", "/pullrequest/") # Fix link for human
        }
        results.append(summary)
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids:
        check_prs(ids)
    else:
        print("Usage: python3 check_specific_prs.py ID1 ID2 ...")
