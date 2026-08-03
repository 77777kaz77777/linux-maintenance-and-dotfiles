#!/bin/bash
# Description: Removes Akonadi/PIM bloat, extra media tools, and cleans caches.

# Exit immediately if a command fails, an unset variable is referenced, or a pipe breaks
set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
LOGDIR="/var/log/packageupdateslogs"
LOGFILE="${LOGDIR}/debloat_fedora.log"

# Ensure the log directory exists with safe permissions
mkdir -p "$LOGDIR"
chmod 755 "$LOGDIR"

# Identify OS release dynamically
FEDORA_VERSION=$(grep -oP '(?<=^VERSION_ID=).*' /etc/os-release | tr -d '"' 2>/dev/null || echo "Fedora")

# Logger Function
log_message() {
    local TIMESTAMP
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "[$TIMESTAMP] $1" | tee -a "$LOGFILE"
}

# -----------------------------------------------------------------------------
# Privilege Check
# -----------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This cleanup script must be run as root or via sudo." >&2
   exit 1
fi

log_message "=== Starting Fedora $FEDORA_VERSION KDE Plasma Debloat & Cleanup ==="

# -----------------------------------------------------------------------------
# 1. Remove KDE PIM (Personal Information Management) & Akonadi
#    Safely target specific packages without wildcards to avoid breaking Plasma dependencies.
# -----------------------------------------------------------------------------
log_message "Removing KDE PIM stack (KMail, KOrganizer, Kontact) and Akonadi..."
dnf remove -y \
    akonadi \
    akonadi-server \
    kmail \
    korganizer \
    kaddressbook \
    kontact \
    knotes \
    akregator \
    kdepim-runtime 2>&1 | tee -a "$LOGFILE" || true

# -----------------------------------------------------------------------------
# 2. Remove Redundant Utilities, Media Players & Games
# -----------------------------------------------------------------------------
log_message "Removing unnecessary default desktop applications..."
dnf remove -y \
    dragonplayer \
    elisa-player \
    kmahjongg \
    kmines \
    ksudoku \
    kpat \
    konversation \
    kmag \
    kmousetool \
    kwrite \
    krdc \
    krfb \
    fedora-media-writer 2>&1 | tee -a "$LOGFILE" || true

# -----------------------------------------------------------------------------
# 3. Clean DNF Packages, Orphans, and System Caches
# -----------------------------------------------------------------------------
log_message "Removing orphaned dependencies..."
dnf autoremove -y 2>&1 | tee -a "$LOGFILE"

log_message "Cleaning DNF metadata and package cache..."
dnf clean all 2>&1 | tee -a "$LOGFILE"

log_message "Trimming systemd journal logs (retaining last 7 days)..."
journalctl --vacuum-time=7d 2>&1 | tee -a "$LOGFILE"

# -----------------------------------------------------------------------------
# 4. User-Level Cache Cleanup (KDE Sycoca and Thumbnail Cache)
# -----------------------------------------------------------------------------
TARGET_USER="${SUDO_USER:-$USER}"
if [[ "$TARGET_USER" != "root" ]]; then
    USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
    
    if [[ -n "$USER_HOME" && -d "$USER_HOME" ]]; then
        log_message "Cleaning KDE system configuration cache for $TARGET_USER..."
        rm -rf "${USER_HOME}/.cache/ksycoca"* 2>/dev/null || true
        
        log_message "Cleaning image thumbnail cache..."
        rm -rf "${USER_HOME}/.cache/thumbnails"* 2>/dev/null || true
    fi
fi

# -----------------------------------------------------------------------------
# Completion
# -----------------------------------------------------------------------------
log_message "=== Debloat and cleanup completed successfully at $(date)! ==="
echo -e "\n[DONE] System debloated successfully! Rebooting is recommended to stop background Akonadi services."
