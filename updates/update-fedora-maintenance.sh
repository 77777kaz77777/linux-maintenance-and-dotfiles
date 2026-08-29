#!/bin/bash
# Full-system maintenance routine for Fedora, covering DNF/Flatpak updates and cache cleanup.
# Exit on error, treat unset variables as error
set -euo pipefail

# Visual formatting constants
BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
RESET="\033[0m"

# -----------------------------------------------------------------------------
# Root Privilege Check & Context Resolution
# -----------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
   echo -e "${BOLD}\033[31m[ERROR] This script must be run as root or via sudo.${RESET}" >&2
   exit 1
fi

# Determine the actual non-root user who invoked sudo
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
FEDORA_VERSION=$(grep -oP '(?<=^VERSION_ID=).*' /etc/os-release | tr -d '"' 2>/dev/null || echo "Fedora")

echo -e "${BOLD}${CYAN}=== Starting Fedora $FEDORA_VERSION System Maintenance ===${RESET}\n"

# -----------------------------------------------------------------------------
# 1. Update DNF Packages & System Flatpaks
# -----------------------------------------------------------------------------
echo -e "${GREEN}[1/5] Updating DNF packages and Flatpaks...${RESET}"
dnf upgrade --refresh -y

if command -v flatpak &> /dev/null; then
    flatpak update -y
    
    # Also update user-level Flatpaks if executed via sudo
    if [[ "$TARGET_USER" != "root" ]]; then
        sudo -u "$TARGET_USER" flatpak update -y || true
    fi
fi

# -----------------------------------------------------------------------------
# 2. Package Cleanup & Orphan Removal
# -----------------------------------------------------------------------------
echo -e "\n${GREEN}[2/5] Cleaning package manager caches and orphan packages...${RESET}"
dnf autoremove -y
dnf clean all

# -----------------------------------------------------------------------------
# 3. Clean Flatpak Unused Runtimes
# -----------------------------------------------------------------------------
if command -v flatpak &> /dev/null; then
    echo -e "\n${GREEN}[3/5] Removing unused Flatpak runtimes...${RESET}"
    flatpak uninstall --unused -y
fi

# -----------------------------------------------------------------------------
# 4. Clear Systemd Logs & User KDE Plasma Cache
# -----------------------------------------------------------------------------
echo -e "\n${GREEN}[4/5] Clearing old systemd logs and KDE Plasma cache...${RESET}"
journalctl --vacuum-time=7d

if [[ "$TARGET_USER" != "root" && -d "$TARGET_HOME" ]]; then
    echo "Cleaning user cache for $TARGET_USER..."
    rm -rf "${TARGET_HOME}/.cache/kiconcache"* 2>/dev/null || true
    rm -rf "${TARGET_HOME}/.cache/kioexec/" 2>/dev/null || true
    rm -rf "${TARGET_HOME}/.cache/ksycoca"* 2>/dev/null || true
    rm -rf "${TARGET_HOME}/.cache/plasma"* 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# 5. Empty User Trash
# -----------------------------------------------------------------------------
echo -e "\n${GREEN}[5/5] Emptying Trash for $TARGET_USER...${RESET}"
if [[ "$TARGET_USER" != "root" && -d "${TARGET_HOME}/.local/share/Trash" ]]; then
    rm -rf "${TARGET_HOME}/.local/share/Trash/files/"* 2>/dev/null || true
    rm -rf "${TARGET_HOME}/.local/share/Trash/info/"* 2>/dev/null || true
fi

echo -e "\n${BOLD}${GREEN}✔ System maintenance completed successfully!${RESET}"
