# 🐧 linux-maintenance-and-dotfiles

A personal repository dedicated to Linux system maintenance, distro updates, terminal configuration files (dotfiles), and custom desktop enhancements.

---

## 🌳 Repository Structure

<!-- START_SECTION:tree -->
```text
linux-maintenance-and-dotfiles/
├── 📁 configs/                           # Terminal & CLI tool dotfiles
│   ├── alacritty.toml                   # Alacritty terminal configuration
│   ├── bash-aliases                     # Shell aliases & shortcuts
│   ├── starship.toml                    # Starship prompt configuration
│   └── topgrade.toml                    # Topgrade auto-updater configuration
├── 📁 desktop-tweaks/                    # UI customization & desktop scripts
│   ├── docs
│   └── set-login-wallpaper.sh           # Display manager wallpaper script
├── 📁 security/                          # Antivirus & system defense utilities
│   ├── clamav-nightly-scan.sh           # Nightly multi-threaded scan script
│   ├── clamav-scan.service              # Systemd service unit executing the nightly scan
│   ├── clamav-scan.timer                # Systemd timer unit scheduling scans at 2:00 AM
│   ├── harden-cachyos.sh                # CachyOS firewall, AppArmor & sysctl hardening
│   ├── run-clamav-scan.sh               # Manual on-demand ClamAV terminal scanner
│   └── update-clamav-signatures.sh      # Manual Freshclam signature updater script
├── 📁 updates/                           # Distro maintenance & update scripts
│   ├── clean-mint.sh                    # Linux Mint package & cache cleanup routine
│   ├── system-cleanup.sh                # Safely cleans temporary files and old system logs.
│   ├── update-Ubuntu                    # Ubuntu system updates
│   ├── update-arch                      # Arch Linux / CachyOS maintenance
│   ├── update-fedora-kde                # Fedora 44 KDE Plasma maintenance & update
│   ├── update-fedora-kde-clean          # Debloat & orphan cleanup for Fedora KDE
│   ├── update-fedora-kde-maintenance    # Fedora 44 KDE Plasma full system maintenance, cache, and cleanup script
│   └── update-linux-mint                # Linux Mint maintenance & update script
└── 📁 utils/                             # General standalone helper scripts
    ├── create_bash_file.sh              # Script generator template
    ├── osi_sec_overview                 # Custom utility tool: OSI Layer Security Overview
    ├── portscanner.py                   # Python port scanner
    ├── toggle-tailscale.sh              # # Tailscale toggle script with exit node prompt
    └── vpn                              # Network/VPN manager script
```
<!-- END_SECTION:tree -->
