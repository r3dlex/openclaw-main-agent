import json
import requests
import websocket
import time

TOKEN = "REDACTED_TOKEN"

def find_tab():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    ports = [18792, 9222]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/json"
            print(f"Trying {url} with auth...")
            resp = requests.get(url, headers=headers, timeout=2)
            print(f"Port {port} status: {resp.status_code}")
            
            if resp.status_code == 200:
                print(f"Connected to browser on port {port}")
                tabs = resp.json()
                for tab in tabs:
                    url = tab.get("url", "")
                    if "login.htmld" in url or "myworkday" in url:
                        # Add token to WS URL if needed for proxy
                        if port == 18792:
                            ws_url = tab.get("webSocketDebuggerUrl")
                            if ws_url and "?" not in ws_url:
                                tab["webSocketDebuggerUrl"] += f"?token={TOKEN}"
                        return tab
        except Exception as e:
            print(f"Failed port {port}: {e}")
            continue
    return None

def click_rib(tab):
    ws_url = tab.get('webSocketDebuggerUrl')
    if not ws_url:
        print("No WebSocket URL found for tab.")
        return "No WS URL"
        
    print(f"Connecting to WS: {ws_url}")
    ws = websocket.create_connection(ws_url)
    
    # 1. Evaluate JS to find the element and click it
    script = """
    (function() {
        // Look for text "RIB" in menuitems
        let items = document.querySelectorAll('div[role="menuitem"], li[role="menuitem"]');
        for (let item of items) {
            if (item.innerText.includes("RIB")) {
                item.click();
                return "Clicked RIB";
            }
        }
        return "RIB not found";
    })();
    """
    
    msg = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": script,
            "returnByValue": True
        }
    }
    
    ws.send(json.dumps(msg))
    result = ws.recv()
    ws.close()
    return result

if __name__ == "__main__":
    tab = find_tab()
    if tab:
        print(f"Found tab: {tab['url']}")
        res = click_rib(tab)
        print(f"Result: {res}")
    else:
        print("No Workday tab found.")
