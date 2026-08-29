#!/bin/bash
# Automated system maintenance and update script for Arch Linux and CachyOS.

# Exit immediately on error, treat unset variables as errors
set -euo pipefail

# Require script to be run as root
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root. Please run with sudo." >&2
   exit 1
fi

# Determine the actual non-root user who invoked sudo (for Flatpaks/AUR)
REAL_USER="${SUDO_USER:-$USER}"

# Log file configuration
LOG_DIR="/var/log/packageupdateslogs"
LOGFILE="$LOG_DIR/update_arch.log"

# Create the log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages with timestamps to both console and log file
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

log_message "--- Starting Arch / CachyOS System Maintenance ---"

# 1. Update package index and upgrade system
log_message "Updating pacman repositories and upgrading system..."
pacman -Syu --noconfirm 2>&1 | tee -a "$LOGFILE"

# 2. Remove orphan packages
log_message "Checking for unnecessary (orphan) packages..."
ORPHANS=$(pacman -Qtdq || true)

if [[ -n "$ORPHANS" ]]; then
    log_message "Removing orphan packages: $ORPHANS"
    # Word splitting is intentional here so pacman receives package list arguments
    # shellcheck disable=SC2086
    pacman -Rns $ORPHANS --noconfirm 2>&1 | tee -a "$LOGFILE"
else
    log_message "No orphan packages found."
fi

# 3. Clean up local package cache
log_message "Cleaning up local package cache..."
if command -v paccache &> /dev/null; then
    log_message "Running paccache (retaining 3 recent versions)..."
    paccache -r 2>&1 | tee -a "$LOGFILE"
    
    log_message "Removing cache of uninstalled packages..."
    paccache -ruk0 2>&1 | tee -a "$LOGFILE"
else
    log_message "paccache not found (pacman-contrib not installed). Falling back to pacman -Sc..."
    pacman -Sc --noconfirm 2>&1 | tee -a "$LOGFILE"
fi

# 4. Update Flatpak applications (System + User level)
if command -v flatpak &> /dev/null; then
    log_message "Updating Flatpak applications..."
    flatpak update -y 2>&1 | tee -a "$LOGFILE"
    
    log_message "Cleaning up unused Flatpak runtimes..."
    flatpak uninstall --unused -y 2>&1 | tee -a "$LOGFILE"
    
    # If invoked via sudo, also trigger a user-level Flatpak cleanup
    if [[ "$REAL_USER" != "root" ]]; then
        log_message "Updating user-level Flatpaks for $REAL_USER..."
        su - "$REAL_USER" -c "flatpak update -y" 2>&1 | tee -a "$LOGFILE" || true
    fi
else
    log_message "Flatpak is not installed. Skipping..."
fi

# Completion message
log_message "All updates and cleanups completed successfully!"
log_message "Log file saved to: $LOGFILE"
echo "" >> "$LOGFILE"
