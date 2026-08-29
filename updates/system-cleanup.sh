#!/bin/bash
# Safe cleanup script for wiping temporary files and old system logs


# Strict mode: exit on error, treat unset variables as error
set -euo pipefail

# Require root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (or with sudo)." >&2
    exit 1
fi

# Configuration Variables
TEMP_DIR="/tmp"
LOG_DIR="/var/log"
DAYS=30

echo "=== Starting System Cleanup: $(date) ==="

# 1. Clean /tmp safely (only delete files older than $DAYS)
if [ -d "$TEMP_DIR" ]; then
    echo "Cleaning temporary files older than $DAYS days in $TEMP_DIR..."
    find "$TEMP_DIR" -type f -mtime +$DAYS -delete 2>/dev/null || true
fi

# 2. Safely truncate or compress old log files (without deleting active log files)
if [ -d "$LOG_DIR" ]; then
    echo "Compressing or truncating old log files in $LOG_DIR..."
    
    # Target archived log files (.gz, .1, .old) older than $DAYS days instead of active log files
    find "$LOG_DIR" -type f \( -name "*.gz" -o -name "*.1" -o -name "*.old" \) -mtime +$DAYS -delete 2>/dev/null || true
fi

# 3. Clean systemd journal logs (if systemd is present)
if command -v journalctl &> /dev/null; then
    echo "Vacuuming systemd journal logs older than ${DAYS}d..."
    journalctl --vacuum-time="${DAYS}d"
fi

echo "=== Cleanup Completed Successfully: $(date) ==="
