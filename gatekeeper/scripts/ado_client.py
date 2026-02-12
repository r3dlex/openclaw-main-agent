import requests, os, base64
from dotenv import load_dotenv

# Load Environment Variables
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Points to workspace/gatekeeper/.env (parent of scripts/)
ENV_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), ".env")
load_dotenv(ENV_PATH)

# Config
ORG = os.getenv("ADO_ORG", "ribdev")
PROJ = os.getenv("ADO_PROJECT", "itwo40")
PAT = os.getenv("ADO_PAT")

if not PAT:
    print("Warning: ADO_PAT not found in .env. API calls will fail.")

BASE_URL = f"https://dev.azure.com/{ORG}/{PROJ}/_apis"

def get_headers():
    if not PAT: return {}
    auth = base64.b64encode(f":{PAT}".encode()).decode()
    return {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

def get_data(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"ADO API Error ({endpoint}): {e}")
        return {}
