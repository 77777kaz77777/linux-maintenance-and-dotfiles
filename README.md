# 🐧 linux-maintenance-and-dotfiles

A personal repository dedicated to Linux system maintenance, distro updates, terminal configuration files (dotfiles), and custom desktop enhancements.

---

## 🌳 Repository Structure

<!-- START_SECTION:tree -->
### 📁 configs/ (Terminal & CLI tool dotfiles)

| File | Description |
|---|---|
| `alacritty.toml` | Configuration file for the Alacritty terminal emulator. |
| `bash-aliases` | Custom shell aliases and command-line shortcuts. |
| `dnf.conf` | Optimized Fedora DNF package manager config tweaked for max download speeds, parallel downloads, and clean dependency management. |
| `fastfetch-laptop1-config.jsonc` | Fastfetch system info configuration for the primary laptop (ASUS ROG Zephyrus G15). |
| `fastfetch-laptop2-config.jsonc` | Fastfetch system info configuration for the secondary laptop (Lenovo ThinkPad T470). |
| `starship.toml` | Custom prompt configuration for Starship. |
| `topgrade.toml` | Configuration settings for the Topgrade auto-updater. |


### 📁 desktop-tweaks/ (UI customization & desktop scripts)

| File | Description |
|---|---|
| `konsole-white-on-black.sh` | Script to force the Konsole terminal background to solid black (#000000) with pure white text. |
| `set-login-wallpaper.sh` | Script to change and apply the display manager wallpaper. |


### 📁 security/ (Antivirus & system defense utilities)

| File | Description |
|---|---|
| `clamav-nightly-scan.sh` | Multi-threaded ClamAV scan script designed to run nightly. |
| `clamav-scan.service` | Systemd service unit responsible for executing the nightly ClamAV scan. |
| `clamav-scan.timer` | Systemd timer unit that schedules the ClamAV scans to run at 2:00 AM |
| `harden-cachyos.sh` | Hardening script to apply firewall, AppArmor, and sysctl security tweaks on CachyOS. |
| `run-clamav-scan.sh` | Script to trigger a manual, on-demand ClamAV scan directly from the terminal. |
| `setup-clamav-fedora.sh` | Automated script to install and set up ClamAV on Fedora. |
| `update-clamav-signatures.sh` | Script to manually trigger Freshclam and update antivirus signatures. |


### 📁 updates/ (Distro maintenance & update scripts)

| File | Description |
|---|---|
| `clean-mint.sh` | Linux Mint package & cache cleanup routine |
| `debloat-fedora-kde.sh` | Removes Akonadi/PIM bloat, extra media tools, Office suites, recommended unused apps, and cleans caches. |
| `system-cleanup.sh` | Safely cleans temporary files and old system logs. |
| `update-arch.sh` | Maintenance & update script for Arch Linux / CachyOS |
| `update-fedora-maintenance.sh` | Full system maintenance, DNF/Flatpak updates, and cache cleanup. |
| `update-fedora.sh` | Automated maintenance, backup, & upgrade script for Fedora KDE |
| `update-mint.sh` | Automated APT, Flatpak, and system cleanup script for Linux Mint. |
| `update-ubuntu.sh` | Automated system update & maintenance script for Ubuntu / Debian |


### 📁 utils/ (General standalone helper scripts)

| File | Description |
|---|---|
| `create-script-template.sh` | Interactive generator that creates an executable Bash script with standard headers and strict error flags. |
| `manage-vpn.sh` | WireGuard connection toggle (WG-Quick UP/DOWN) |
| `osi-security-overview.sh` | Custom utility tool: OSI Layer Security Overview |
| `port-scanner.py` | Educational multi-threaded TCP socket scanner (College Project) |
| `setup.py` | (Work in Progress) Automated Python workstation bootstrap, toolstack installer, and repository script deployment with GUI. |
| `system-health-report.sh` | Generates a quick diagnostic report of system health, disk usage, and failed systemd services. |
| `toggle-tailscale.sh` | Tailscale toggle script with exit node prompt |
<!-- END_SECTION:tree -->
