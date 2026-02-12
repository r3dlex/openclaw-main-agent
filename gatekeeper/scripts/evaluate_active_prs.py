from ado_client import get_data
from evaluate_pr import evaluate
import json

def process_active_prs():
    print("Fetching active PRs...")
    prs = get_data("git/pullrequests", {"searchCriteria.status": "active", "api-version": "7.0"})
    
    if not prs:
        print("No active PRs found.")
        return

    # Limit to 20 for quick check
    # active_prs = prs.get("value", [])[:20] 
    active_prs = prs.get("value", [])
    print(f"Found {len(active_prs)} active PRs. Evaluating...")
    
    safe_prs = []
    risky_prs = []
    
    for pr in active_prs:
        pr_id = pr["pullRequestId"]
        result = evaluate(pr_id)
        
        if result["score"] > 8:
            safe_prs.append(result)
        else:
            risky_prs.append(result)
            
    print("\n=== SAFE PRs (Score > 8) ===")
    for p in safe_prs:
        print(f"[Score: {p['score']}] PR #{p['id']}: {p['title']} ({p['author']}) - {p['url']}")
        
    print("\n=== RISKY PRs (Score <= 8) ===")
    for p in risky_prs:
        print(f"[Score: {p['score']}] PR #{p['id']}: {p['title']} ({p['author']}) - Reasons: {', '.join(p['reasons'])}")

    # Save results to a file for potential approval step
    with open("gatekeeper/data/safe_prs.json", "w") as f:
        json.dump(safe_prs, f, indent=2)

if __name__ == "__main__":
    process_active_prs()
