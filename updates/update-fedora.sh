#!/bin/bash
# Description: Automated maintenance & upgrade script for Fedora (KDE / Workstation)

# Exit immediately on unhandled error, unset variable, or piped command failure
set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
LOGDIR="/var/log/packageupdateslogs"
LOGFILE="${LOGDIR}/update_fedora.log"
MAX_LOG_SIZE_KB=5000  # Rotate log if it exceeds ~5MB

# Identify active desktop user (for desktop notifications and user flatpaks)
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_UID=$(id -u "$TARGET_USER" 2>/dev/null || echo 1000)

# Fetch OS release details dynamically
FEDORA_VERSION=$(grep -oP '(?<=^VERSION_ID=).*' /etc/os-release | tr -d '"' 2>/dev/null || echo "Fedora")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
# Root Privilege Check
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This script must be run as root or via sudo." >&2
   exit 1
fi

# Ensure log directory exists with safe permissions
mkdir -p "$LOGDIR"
chmod 755 "$LOGDIR"

# Simple Log Rotation
if [[ -f "$LOGFILE" ]] && [[ $(du -k "$LOGFILE" | cut -f1) -ge $MAX_LOG_SIZE_KB ]]; then
   mv "$LOGFILE" "${LOGFILE}.bak.$(date +%Y%m%d%H%M%S)"
   touch "$LOGFILE"
fi

# Write timestamped output to terminal and log file
log_message() {
    local TIMESTAMP
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "[$TIMESTAMP] $1" | tee -a "$LOGFILE"
}

# Trigger Desktop Notifications
send_notification() {
    local TITLE="$1"
    local BODY="$2"
    local URGENCY="${3:-normal}" # low, normal, critical
    
    if command -v notify-send &>/dev/null && [[ "$TARGET_USER" != "root" ]]; then
        sudo -u "$TARGET_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${TARGET_UID}/bus" \
            notify-send -u "$URGENCY" -a "System Updater" "$TITLE" "$BODY" || true
    fi
}

# Cleanup hook in case script encounters a fatal error
trap_failure() {
    log_message "[FATAL ERROR] Maintenance script aborted prematurely!"
    send_notification "System Maintenance Failed" "An error occurred during system updates. Check $LOGFILE for details." "critical"
}
trap trap_failure ERR

# -----------------------------------------------------------------------------
# Main Maintenance Routine
# -----------------------------------------------------------------------------
log_message "=================================================="
log_message "Starting System Maintenance (Fedora $FEDORA_VERSION)"
log_message "Running on behalf of user: $TARGET_USER"
log_message "=================================================="

send_notification "System Maintenance Started" "Updating packages and Flatpaks..." "low"

# 1. Update Fedora RPM Packages (DNF / DNF5)
log_message "Refreshing RPM repositories and upgrading packages..."
dnf upgrade --refresh -y 2>&1 | tee -a "$LOGFILE"

# 2. Package Cleanup & Orphan Removal
log_message "Removing orphan dependencies and clearing package cache..."
dnf autoremove -y 2>&1 | tee -a "$LOGFILE"
dnf clean dbcache expire-cache 2>&1 | tee -a "$LOGFILE"

# 3. System-Wide & User Flatpak Updates
if command -v flatpak &>/dev/null; then
    log_message "Updating System Flatpaks..."
    flatpak update -y 2>&1 | tee -a "$LOGFILE"
    
    log_message "Cleaning unused Flatpak runtimes..."
    flatpak uninstall --unused -y 2>&1 | tee -a "$LOGFILE"

    # Update User-level Flatpaks if executed via sudo
    if [[ "$TARGET_USER" != "root" ]]; then
        log_message "Updating User Flatpaks for $TARGET_USER..."
        sudo -u "$TARGET_USER" flatpak update -y 2>&1 | tee -a "$LOGFILE" || true
    fi
fi

# 4. Hardware Firmware Updates (fwupd)
if command -v fwupdmgr &>/dev/null; then
    log_message "Checking for Hardware Firmware Updates..."
    fwupdmgr refresh --quiet 2>&1 | tee -a "$LOGFILE" || true
    fwupdmgr get-updates 2>&1 | tee -a "$LOGFILE" || true
fi

# 5. Optional KDE Plasma Cache Cleanup
if [[ "$TARGET_USER" != "root" ]]; then
    USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
    if [[ -n "$USER_HOME" && -d "$USER_HOME" ]]; then
        if ls "${USER_HOME}/.cache/ksycoca"* 1>/dev/null 2>&1; then
            log_message "Cleaning KDE System Configuration Cache..."
            rm -rf "${USER_HOME}/.cache/ksycoca"* 2>/dev/null || true
        fi
    fi
fi

# -----------------------------------------------------------------------------
# Completion
# -----------------------------------------------------------------------------
log_message "All updates completed successfully at $(date)!"
send_notification "System Maintenance Complete" "Your Fedora system is fully up to date." "normal"

# Clear error trap prior to successful exit
trap - ERR
exit 0
