const WebSocket = require('ws');
const http = require('http');

const TOKEN = "REDACTED_TOKEN";
const PORT = 18792;

function getTabs() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'localhost',
            port: PORT,
            path: `/json?token=${TOKEN}`,
            headers: { 'Authorization': `Bearer ${TOKEN}` }
        };
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    resolve(JSON.parse(data));
                } else {
                    reject(`Status: ${res.statusCode}`);
                }
            });
        });
        req.on('error', reject);
        req.end();
    });
}

async function run() {
    try {
        const tabs = await getTabs();
        const tab = tabs.find(t => t.url.includes("workday.com") || t.title.includes("Workday"));
        if (!tab) {
            console.log("Workday tab not found.");
            return;
        }
        
        let wsUrl = tab.webSocketDebuggerUrl;
        if (wsUrl && !wsUrl.includes("token=")) {
            wsUrl += `?token=${TOKEN}`;
        }
        
        console.log(`Connecting to ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        
        ws.on('open', () => {
            console.log("Connected to WS");
            // Evaluate JS to click Approve
            const msg = {
                id: 1,
                method: "Runtime.evaluate",
                params: {
                    expression: `
                        (function() {
                            // Try to find "Approve" button
                            let buttons = document.querySelectorAll('button, div[role="button"]');
                            for (let b of buttons) {
                                if (b.innerText.trim() === "Approve") {
                                    b.click();
                                    return "Clicked Approve";
                                }
                            }
                            return "Approve button not found";
                        })()
                    `,
                    returnByValue: true
                }
            };
            ws.send(JSON.stringify(msg));
        });
        
        ws.on('message', (data) => {
            const res = JSON.parse(data);
            if (res.id === 1) {
                console.log("Result:", res.result.result.value);
                ws.close();
            }
        });
        
        ws.on('error', (e) => console.error("WS Error:", e));
        
    } catch (e) {
        console.error("Error:", e);
    }
}

run();
