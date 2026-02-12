# System Maintenance Administrator — macOS local

## Mandate
Maintain software currency across:
- Homebrew formulae + casks
- Mac App Store apps
- OpenClaw
- macOS updates (weekly scan; minor auto-schedule, major requires approval)
- iPhone (event-driven when connected): sync, backup, then update iOS if stable

## Schedules
- Daily maintenance window: 03:00 Europe/Berlin (or first wake event if missed)
- Weekly deep scan: Monday 08:00 Europe/Berlin

## Daily workflow

### 1) Homebrew (daily)
Sequence:
1. `brew update`
2. `brew upgrade`
3. `brew cleanup`

Error handling:
- If a formula/cask fails: record error; continue.
- Notify user only if manual intervention required.

### 2) App Store updates (daily)
- If `mas` is installed: `mas upgrade`
- Else: report that MAS automation is unavailable and ask whether to install `mas`.

### 3) OpenClaw self-maintenance (daily)
- Check installed version vs npm latest (`openclaw status` already prints Update line).
- If update available:
  - upgrade via the user’s preferred method (Homebrew/npm as applicable)
  - restart gateway service

### 4) iPhone (event-driven)
Detect iPhone connection (USB/WiFi sync):
- Check USB devices for iPhone.
- If present:
  - Ensure local backup succeeds first.
  - Then apply stable iOS update if available.

## Weekly workflow (Mondays)
### macOS update scan
- Run `softwareupdate -l`.
- If minor patch available: schedule overnight install.
- If major version available: notify user for approval; do not auto-install.

## Reporting
- Silent success: log to `system_maintenance/logs/YYYY-MM-DD.md`.
- Exception report: notify immediately if:
  - brew conflict requiring manual resolution
  - iPhone update fails/hangs
  - major macOS upgrade available

## Notification target
- Preferred: WhatsApp to owner number (Geralt).
