# 🐧 linux-maintenance-and-dotfiles

A personal repository dedicated to Linux system maintenance, distro updates, terminal configuration files (dotfiles), and custom desktop enhancements.

---

## 🌳 Repository Structure

<!-- START_SECTION:tree -->
```text
linux-maintenance-and-dotfiles/
├── 📁 configs/                          # Terminal & CLI tool dotfiles
│   ├── alacritty.toml                  # Alacritty terminal configuration
│   ├── bash-aliases                    # Shell aliases & shortcuts
│   ├── dnf.conf                        # Optimized Fedora DNF package manager configuration tuned for maximum download speeds, parallel downloads, and clean dependency management.
│   ├── starship.toml                   # Starship prompt configuration
│   └── topgrade.toml                   # Topgrade auto-updater configuration
├── 📁 desktop-tweaks/                   # UI customization & desktop scripts
│   ├── docs
│   ├── konsole-white-on-black.sh       # Sets terminal background to solid black (#000000), default text to pure white
│   └── set-login-wallpaper.sh          # Display manager wallpaper script
├── 📁 security/                         # Antivirus & system defense utilities
│   ├── clamav-nightly-scan.sh          # Nightly multi-threaded scan script
│   ├── clamav-scan.service             # Systemd service unit executing the nightly scan
│   ├── clamav-scan.timer               # Systemd timer unit scheduling scans at 2:00 AM
│   ├── harden-cachyos.sh               # CachyOS firewall, AppArmor & sysctl hardening
│   ├── run-clamav-scan.sh              # Manual on-demand ClamAV terminal scanner
│   └── update-clamav-signatures.sh     # Manual Freshclam signature updater script
├── 📁 updates/                          # Distro maintenance & update scripts
│   ├── clean-mint.sh                   # Linux Mint package & cache cleanup routine
│   ├── debloat-fedora-kde.sh           # Removes Akonadi/PIM bloat, extra media tools, and cleans caches.
│   ├── system-cleanup.sh               # Safely cleans temporary files and old system logs.
│   ├── update-arch.sh                  # Maintenance & update script for Arch Linux / CachyOS
│   ├── update-fedora-maintenance.sh    # Full system maintenance, DNF/Flatpak updates, and cache cleanup.
│   ├── update-fedora.sh                # Automated maintenance, backup, & upgrade script for Fedora KDE
│   ├── update-mint.sh                  # Automated APT, Flatpak, and system cleanup script for Linux Mint.
│   └── update-ubuntu.sh                # Automated system update & maintenance script for Ubuntu / Debian
└── 📁 utils/                            # General standalone helper scripts
    ├── create-script-template.sh       # Interactive generator that creates an executable Bash script with standard headers and strict error flags.
    ├── manage-vpn.sh                   # WireGuard connection toggle (WG-Quick UP/DOWN)
    ├── osi-security-overview.sh        # Custom utility tool: OSI Layer Security Overview
    ├── port-scanner.py                 # Educational multi-threaded TCP socket scanner (College Project)
    ├── setup.py                        # Automated Python workstation bootstrap, toolstack installer, and repository script deployment.
    └── toggle-tailscale.sh             # # Tailscale toggle script with exit node prompt
```
<!-- END_SECTION:tree -->
