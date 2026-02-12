from ado_client import get_data
import json

def inspect_pr(pr_id):
    pr = get_data(f"git/pullrequests/{pr_id}", {"api-version": "7.0"})
    if not pr:
        print("PR not found")
        return

    print(json.dumps(pr.get("reviewers", []), indent=2))

if __name__ == "__main__":
    inspect_pr("40170")
