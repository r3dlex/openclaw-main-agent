# OpenClaw Workspace

Personal AI assistant workspace managed by [OpenClaw](https://github.com/openclaw/openclaw).

## 🤖 Robo

Experimental AI assistant running on Mac mini. See `IDENTITY.md` for details.

## 📁 Structure

- `agent_*/` - Agent scripts and configs
- `memory/` - Daily logs and long-term memory
- `Backup_Zero/` - Archive for outdated files

## 🔐 Secrets

This workspace contains sensitive data. Protected via `.gitignore`:
- `*client_secret*`
- `*token*.json`
- `.env`

## 🛠️ Tools

- Email: IMAP (6 accounts) + Gmail API
- Calendar: Google Calendar API
- Azure DevOps: PR auto-approval
- Messaging: WhatsApp + Telegram
- Browser: Chrome with Relay extension

## 📅 Active Cron Jobs

- Email Tidy (hourly)
- NewsOps Morning/Evening
- HR Tasks (Mon-Fri)
- Weekly Archive

---
*Automated by Robo 🤖*
