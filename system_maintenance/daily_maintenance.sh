#!/bin/bash
LOGfile="REDACTED_PATH/.openclaw/workspace/system_maintenance/logs/$(date +%Y-%m-%d).md"
echo "# System Maintenance Log - $(date)" > "$LOGfile"

# 1. Homebrew
echo "## 1. Homebrew" >> "$LOGfile"
echo '```' >> "$LOGfile"
# specific path to avoid path issues
BREW="/opt/homebrew/bin/brew"
if [ -x "$BREW" ]; then
    $BREW update >> "$LOGfile" 2>&1
    $BREW upgrade >> "$LOGfile" 2>&1
    $BREW cleanup >> "$LOGfile" 2>&1
    BREW_EXIT=$?
else
    echo "Homebrew not found at $BREW" >> "$LOGfile"
    BREW_EXIT=1
fi
echo '```' >> "$LOGfile"

# 2. MAS
echo "## 2. MAS" >> "$LOGfile"
if command -v mas &> /dev/null; then
    echo '```' >> "$LOGfile"
    mas upgrade >> "$LOGfile" 2>&1
    MAS_EXIT=$?
    echo '```' >> "$LOGfile"
else
    echo "MAS (Mac App Store CLI) not installed." >> "$LOGfile"
    MAS_EXIT=0
fi

# 3. OpenClaw
echo "## 3. OpenClaw" >> "$LOGfile"
# Check via npm
if npm outdated -g openclaw-cli | grep -q openclaw-cli; then
    echo "Update available. Updating..." >> "$LOGfile"
    npm install -g openclaw-cli >> "$LOGfile" 2>&1
    OPENCLAW_UPDATED=1
else
    echo "OpenClaw is up to date." >> "$LOGfile"
    OPENCLAW_UPDATED=0
fi

# 4. iPhone
echo "## 4. iPhone" >> "$LOGfile"
if system_profiler SPUSBDataType 2>/dev/null | grep -q "iPhone"; then
     echo "iPhone detected." >> "$LOGfile"
     if command -v idevicebackup2 &> /dev/null; then
         echo "Starting backup..." >> "$LOGfile"
         # This might fail if the device is locked/unpaired
         idevicebackup2 backup check >> "$LOGfile" 2>&1 || true
         idevicebackup2 backup safe >> "$LOGfile" 2>&1
         BACKUP_EXIT=$?
         if [ $BACKUP_EXIT -eq 0 ]; then
             echo "Backup successful." >> "$LOGfile"
         else
             echo "Backup failed. (Is device unlocked/trusted?)" >> "$LOGfile"
         fi
     else
         echo "idevicebackup2 (libimobiledevice) not found. Skipping backup." >> "$LOGfile"
         # Not a critical failure of the *maintenance*, just missing capability
         BACKUP_EXIT=0 
     fi
else
     echo "No iPhone detected via USB." >> "$LOGfile"
     BACKUP_EXIT=0
fi

# Determine exit code for the agent
# 0 = Success, no restart
# 1 = Error (notify user)
# 2 = Success, restart needed (OpenClaw updated)

EXIT_CODE=0

if [ $BREW_EXIT -ne 0 ] || [ $BACKUP_EXIT -ne 0 ]; then
    EXIT_CODE=1
elif [ $OPENCLAW_UPDATED -eq 1 ]; then
    EXIT_CODE=2
fi

echo "## Status" >> "$LOGfile"
echo "Exit Code: $EXIT_CODE" >> "$LOGfile"

exit $EXIT_CODE
