#!/bin/bash
# Description: Automated maintenance, backup, & upgrade script for Fedora KDE

# Exit immediately on unhandled error, unset variable, or piped command failure
set -euo pipefail

# -----------------------------------------------------------------
# Formatting & Output Helpers
# -----------------------------------------------------------------
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# -----------------------------------------------------------------
# 1. Privilege & Pre-check Verification
# -----------------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root or with sudo."
    exit 1
fi

log_info "Starting Fedora KDE maintenance and update routine..."

# -----------------------------------------------------------------
# 2. Automated Pre-Update Btrfs Snapshot
# -----------------------------------------------------------------
SNAP_NUM=""
if command -v snapper &> /dev/null; then
    log_info "Creating pre-update Snapper snapshot..."
    SNAP_NUM=$(snapper -c root create --type pre --cleanup-algorithm number --description "update-fedora.sh pre-update" --print-number || true)
    
    if [ -n "$SNAP_NUM" ]; then
        log_success "Created pre-update snapshot #${SNAP_NUM}."
    else
        log_warn "Snapper snapshot creation skipped or failed. Proceeding with update..."
    fi
else
    log_warn "Snapper CLI not found. Skipping pre-update snapshot."
fi

# -----------------------------------------------------------------
# 3. System Package Updates (DNF)
# -----------------------------------------------------------------
log_info "Refreshing metadata and upgrading DNF packages..."
dnf upgrade --refresh -y

# -----------------------------------------------------------------
# 4. Flatpak & Firmware Updates
# -----------------------------------------------------------------
if command -v flatpak &> /dev/null; then
    log_info "Updating Flatpak applications..."
    flatpak update -y
    
    log_info "Cleaning unused Flatpak runtimes..."
    flatpak uninstall --unused -y || true
fi

if command -v fwupdmgr &> /dev/null; then
    log_info "Checking device firmware updates..."
    fwupdmgr refresh > /dev/null 2>&1 || true
    fwupdmgr update -y || true
fi

# -----------------------------------------------------------------
# 5. Git Source Packages Updates (grub-btrfs)
# -----------------------------------------------------------------
TARGET_USER="${SUDO_USER:-$USER}"
USER_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
GRUB_BTRFS_DIR="${USER_HOME}/grub-btrfs"

if [ -d "$GRUB_BTRFS_DIR/.git" ]; then
    log_info "Checking for grub-btrfs git repository updates..."
    git -C "$GRUB_BTRFS_DIR" pull || log_warn "Failed to pull updates for grub-btrfs."
    make -C "$GRUB_BTRFS_DIR" install || log_warn "Failed to reinstall grub-btrfs."
    restorecon -Rv /usr/bin/grub-btrfs* /usr/lib/systemd/system/grub-btrfsd.service > /dev/null 2>&1 || true
    systemctl daemon-reload || true
    systemctl restart grub-btrfsd || true
    log_success "grub-btrfs up to date."
fi

# -----------------------------------------------------------------
# 6. System Cleanup
# -----------------------------------------------------------------
log_info "Removing orphan packages and clearing DNF cache..."
dnf autoremove -y
dnf clean all

# -----------------------------------------------------------------
# 7. Post-Update Snapshot & GRUB Menu Refresh
# -----------------------------------------------------------------
if [ -n "$SNAP_NUM" ] && command -v snapper &> /dev/null; then
    log_info "Creating post-update Snapper pair snapshot for #${SNAP_NUM}..."
    snapper -c root create --type post --pre-number "$SNAP_NUM" --cleanup-algorithm number --description "update-fedora.sh post-update" || true
fi

if [ -f /boot/grub2/grub.cfg ]; then
    log_info "Regenerating GRUB boot menu (updating grub-btrfs entries)..."
    grub2-mkconfig -o /boot/grub2/grub.cfg || true
fi

log_success "Maintenance complete! System updated, cleaned, and snapshots registered in GRUB."
