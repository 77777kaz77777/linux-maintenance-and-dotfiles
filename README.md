# 🐧 linux-maintenance-and-dotfiles

A personal repository dedicated to Linux system maintenance, distro updates, terminal configuration files (dotfiles), and custom desktop enhancements.

---

## 🌳 Repository Structure

```text
linux-maintenance-and-dotfiles/
├── 📁 updates/                  # Distro maintenance & update scripts
│   ├── update-arch              # Arch Linux / CachyOS maintenance
│   ├── update-Ubuntu            # Ubuntu system updates
│   ├── Clean Mint 22.3          # Linux Mint cleanup routine
│   ├── Cleanup Script           # Disk & system cleanup utility
│   └── new update               # Miscellaneous update script
│
├── 📁 configs/                  # Terminal & CLI tool dotfiles
│   ├── alacritty.toml          # Alacritty terminal configuration
│   ├── mystarshipconf.toml     # Starship prompt configuration
│   ├── mytopgradeconf.toml     # Topgrade auto-updater configuration
│   └── alias                    # Shell aliases & shortcuts
│
├── 📁 desktop-tweaks/          # UI customization & desktop scripts
│   ├── blackloginscreenwallpaper.sh  # Display manager wallpaper script
│   └── move_ubuntu_button.txt        # GNOME / Desktop layout modification guide
│
├── 📁 security/                # Antivirus & system defense utilities
│   ├── secure-cachyos.sh       # CachyOS firewall, AppArmor & sysctl hardening
│   ├── clamav                  # ClamAV scanner integration
│   └── ClamAV Signature Update # Antivirus database updater
│
└── 📁 utils/                    # General standalone helper scripts
    ├── vpn                      # Network/VPN manager script
    ├── ps.py                    # Process monitoring Python utility
    ├── create_bash_file.sh      # Script generator template
    └── improved osi             # Custom utility tool
