#!/bin/bash
# Description: Automated APT, Flatpak, and system cleanup script for Linux Mint.

# Exit immediately if a command exits with a non-zero status
set -e

# Require root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: This maintenance script must be run as root (use sudo)." >&2
  exit 1
fi

# Log configuration
LOGDIR="/var/log/packageupdateslogs"
LOGFILE="$LOGDIR/update_mint.log"

# Identify non-root user for user-level Flatpak updates
TARGET_USER="${SUDO_USER:-$USER}"

# Ensure the log directory exists with safe permissions
mkdir -p "$LOGDIR"
chmod 755 "$LOGDIR"

# Function to log timestamped messages
log_message() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1" | tee -a "$LOGFILE"
}

log_message "=== Starting Linux Mint System Maintenance ==="

# 1. Update APT Package Index
log_message "Updating APT package index..."
apt-get update -q -y 2>&1 | tee -a "$LOGFILE"

# 2. Upgrade APT Packages
log_message "Upgrading installed APT packages..."
DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y -q 2>&1 | tee -a "$LOGFILE"

# 3. Remove Unnecessary APT Packages
log_message "Removing unnecessary orphaned dependencies..."
apt-get autoremove -y -q 2>&1 | tee -a "$LOGFILE"

# 4. Clean APT Package Cache
log_message "Cleaning local package cache..."
apt-get autoclean -q 2>&1 | tee -a "$LOGFILE"

# 5. Update System & User Flatpaks
if command -v flatpak &> /dev/null; then
    log_message "Updating system-wide Flatpak applications..."
    flatpak update -y 2>&1 | tee -a "$LOGFILE"

    log_message "Cleaning unused Flatpak runtimes..."
    flatpak uninstall --unused -y 2>&1 | tee -a "$LOGFILE"

    # Update user-level Flatpaks if executed via sudo
    if [ "$TARGET_USER" != "root" ]; then
        log_message "Updating user-level Flatpaks for $TARGET_USER..."
        sudo -u "$TARGET_USER" flatpak update -y 2>&1 | tee -a "$LOGFILE" || true
    fi
else
    log_message "Flatpak is not installed. Skipping Flatpak updates..."
fi

# Completion Message
log_message "All updates and cleanups completed successfully!"
echo "" >> "$LOGFILE"
