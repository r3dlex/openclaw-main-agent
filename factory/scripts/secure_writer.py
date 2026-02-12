import sys, json, os

# 1. Load Governance
GOV_FILE = "REDACTED_PATH/.openclaw/workspace/factory/governance/scopes.json"
try:
    with open(GOV_FILE) as f:
        SCOPES = json.load(f)
except FileNotFoundError:
    print(f"ERROR: Governance file not found at {GOV_FILE}")
    sys.exit(1)

def write(stack, path, content):
    # 2. Validate Scope
    if stack not in SCOPES:
        print(f"ERROR: Unknown stack '{stack}'")
        sys.exit(1)
        
    allowed_exts = SCOPES[stack]["extensions"]
    if not any(path.endswith(ext) for ext in allowed_exts):
        print(f"SECURITY BLOCK: The '{stack}' persona cannot write to {path}")
        sys.exit(1)

    # 3. Write
    os.makedirs(os.path.dirname(path), exist_ok=True) # Ensure dir exists
    with open(path, "w") as f:
        f.write(content)
    print(f"SUCCESS: Wrote {path} (Stack: {stack})")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: secure_writer.py <stack> <path> <content>")
        sys.exit(1)
    write(sys.argv[1], sys.argv[2], sys.argv[3])
