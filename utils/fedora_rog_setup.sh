#!/bin/bash
# Optimization and Setup Script for ASUS ROG Zephyrus G15 on Fedora 44 KDE
# Hardware Target: AMD Ryzen 9 6900HS & NVIDIA RTX 3070 Ti

echo "Starting ASUS ROG optimization setup for Fedora 44..."

# 1. Purge the deprecated COPR repository and legacy packages
echo "Purging old lukenukem/asus-linux COPR repository and old packages..."
sudo dnf copr remove -y lukenukem/asus-linux
sudo dnf remove -y asusctl supergfxctl asusctl-rog-gui

# 2. Install the Terra repository 
echo "Adding Terra repository..."
sudo dnf install -y --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release

# 3. Update the system package cache
echo "Refreshing package cache..."
sudo dnf update -y --refresh

# 4. Install core ASUS utilities and allow replacement of default switcheroo
echo "Installing asusctl, cardwire, and ROG Control Center..."
sudo dnf install -y --allowerasing asusctl cardwire asusctl-rog-gui

# 5. Enable the cardwire daemon
echo "Enabling cardwire daemon..."
sudo systemctl enable --now cardwired.service

echo "Setup complete. A system reboot is required for GPU module loading to finalize."
