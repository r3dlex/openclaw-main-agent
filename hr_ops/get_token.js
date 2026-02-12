const fs = require('fs');
const config = JSON.parse(fs.readFileSync('REDACTED_PATH/.openclaw/openclaw.json', 'utf8'));
console.log(config.gateway.auth.token);
