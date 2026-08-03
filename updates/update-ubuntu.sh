#!/bin/bash
# Description: Automated system update & maintenance script for Ubuntu / Debian

# Exit immediately if a command exits with a non-zero status
set -e

# Require root privileges
if [ "$EUID" -ne 0 ]; then 
  echo "Error: Please run as root (e.g., sudo ./update-ubuntu.sh)" >&2
  exit 1
fi

# Configuration Variables
LOG_DIR="/var/log/packageupdateslogs"
LOGFILE="$LOG_DIR/update_ubuntu.log"

# Determine non-root user for desktop notifications safely
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo "$USER")}"
USER_ID=$(id -u "$REAL_USER" 2>/dev/null || echo "1000")

# Initialize logging directory
mkdir -p "$LOG_DIR"

# Function to write timestamped log messages to stdout and logfile
log_info() {
    local msg="$1"
    echo "[( $(date +'%Y-%m-%d %H:%M:%S') )] $msg" | tee -a "$LOGFILE"
}

# Safely send desktop notifications without throwing set -e errors
notify() {
    local message="$1"
    if [ "$REAL_USER" != "root" ] && command -v notify-send &> /dev/null; then
        sudo -u "$REAL_USER" \
          DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$USER_ID/bus" \
          notify-send "System Update" "$message" || true
    fi
}

log_info "--- Starting Ubuntu System Maintenance ---"

# 1. Handle APT & DPKG Locks
log_info "Checking for package manager locks..."
LOCK_FILES=("/var/lib/dpkg/lock-frontend" "/var/lib/dpkg/lock" "/var/lib/apt/lists/lock")

for lock_file in "${LOCK_FILES[@]}"; do
    while fuser "$lock_file" >/dev/null 2>&1; do
        log_info "Waiting for background package manager to release $lock_file..."
        sleep 5
    done
done

# 2. Update APT Package Repositories & Install Upgrades
log_info "Updating APT package index..."
apt-get update -q -y 2>&1 | tee -a "$LOGFILE"

log_info "Performing full APT distribution upgrade..."
# Non-interactive flag prevents prompts from stopping the script
DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y 2>&1 | tee -a "$LOGFILE"

# 3. Update Snaps (Ubuntu Desktop)
if command -v snap &> /dev/null; then
    log_info "Refreshing Snap packages..."
    snap refresh 2>&1 | tee -a "$LOGFILE"
else
    log_info "Snap package manager not found. Skipping..."
fi

# 4. Update Flatpaks
if command -v flatpak &> /dev/null; then
    log_info "Updating Flatpak applications..."
    flatpak update -y 2>&1 | tee -a "$LOGFILE"
    
    # Also update user-level flatpaks if run via sudo
    if [ "$REAL_USER" != "root" ]; then
        sudo -u "$REAL_USER" flatpak update -y 2>&1 | tee -a "$LOGFILE" || true
    fi
else
    log_info "Flatpak package manager not found. Skipping..."
fi

# 5. Cleanup Obsolete Packages & Caches
log_info "Removing unneeded dependencies and cleaning APT cache..."
apt-get autoremove -y 2>&1 | tee -a "$LOGFILE"
apt-get autoclean -y 2>&1 | tee -a "$LOGFILE"

# 6. Check Reboot Status
if [ -f /var/run/reboot-required ]; then
    log_info "WARNING: A system reboot is required to complete updates."
    notify "Update complete. A system reboot is required."
else
    log_info "Update complete. No reboot necessary."
    notify "System is up to date."
fi

log_info "All updates and cleanups completed successfully!"
echo "" >> "$LOGFILE"
