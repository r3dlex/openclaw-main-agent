from ado_client import get_data, get_headers, BASE_URL
import requests

def get_my_id():
    # https://dev.azure.com/{organization}/_apis/connectionData?api-version=7.0
    # BASE_URL is .../{project}/_apis
    # We need to go up one level to org.
    
    # ado_client.BASE_URL = f"https://dev.azure.com/{ORG}/{PROJ}/_apis"
    # We want https://dev.azure.com/{ORG}/_apis/connectionData
    
    parts = BASE_URL.split(f"/_apis")
    root_url = parts[0] # https://dev.azure.com/{ORG}/{PROJ}
    # split again to get org
    # Actually simpler:
    org_url = BASE_URL.split(f"/itwo40")[0] # Assuming project is itwo40
    # Better: just use the ORG env var if available, or parse BASE_URL safely.
    
    # Let's try relative to BASE_URL
    # connectionData is at the root of the collection/org usually.
    
    url = f"{BASE_URL}/../connectionData" # Try project level first? No, usually org level.
    # Let's try constructing it manually.
    
    import os
    ORG = os.getenv("ADO_ORG", "ribdev")
    url = f"https://dev.azure.com/{ORG}/_apis/connectionData?api-version=7.0"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        print(f"My ID: {data['authenticatedUser']['id']}")
        print(f"My Name: {data['authenticatedUser']['providerDisplayName']}")
        return data['authenticatedUser']['id']
    except Exception as e:
        print(f"Error fetching identity: {e}")
        return None

if __name__ == "__main__":
    get_my_id()
