#!/bin/bash
# Description: Fedora 44 KDE Plasma full system maintenance, cache, and cleanup script

# Terminate on error
set -e

# Visual formatting
BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}=== Starting Fedora 44 KDE System Maintenance ===${RESET}\n"

# 1. Update DNF Packages & Flatpaks
echo -e "${GREEN}[1/5] Updating DNF packages and Flatpaks...${RESET}"
sudo dnf upgrade --refresh -y
if command -v flatpak &> /dev/null; then
    flatpak update -y
fi

# 2. Package Cleanup & Orphan Removal
echo -e "\n${GREEN}[2/5] Cleaning package manager caches and orphan packages...${RESET}"
sudo dnf autoremove -y
sudo dnf clean all

# 3. Clean Flatpak Unused Runtimes
if command -v flatpak &> /dev/null; then
    echo -e "\n${GREEN}[3/5] Removing unused Flatpak runtimes...${RESET}"
    flatpak uninstall --unused -y
fi

# 4. Clear KDE Plasma Cache & System Logs
echo -e "\n${GREEN}[4/5] Clearing KDE Plasma cache & old systemd logs...${RESET}"
# Vacuum systemd journal logs older than 7 days
sudo journalctl --vacuum-time=7d

# Clear user cache (KDE icons, KImageCache, Plasma components)
rm -rf ~/.cache/kiconcache*
rm -rf ~/.cache/kioexec/
rm -rf ~/.cache/ksycoca5*
rm -rf ~/.cache/ksycoca6*
rm -rf ~/.cache/plasma*

# 5. Empty User Trash
echo -e "\n${GREEN}[5/5] Emptying Trash...${RESET}"
rm -rf ~/.local/share/Trash/files/*
rm -rf ~/.local/share/Trash/info/*

echo -e "\n${BOLD}${GREEN}✔ System maintenance completed successfully!${RESET}"
