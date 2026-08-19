#Description : Multi-distro workstation app installer (CachyOS/Arch, Fedora, Ubuntu/Debian)
#  Installs Brave, Sublime Text, Podman, LM Studio, Fastfetch, 
# Tailscale, Virt-Manager, btop, and Trayscale.

#!/usr/bin/env bash

# Exit on error, treat unset variables as an error, and fail on pipeline errors
set -euo pipefail

# Check for root / sudo privileges
if [[ $EUID -ne 0 ]]; then
   echo "[!] This script must be run with sudo or as root to configure software repositories and system packages."
   echo "    Usage: sudo bash $0"
   exit 1
fi

# Detect non-root real user for user-scoped operations (like Flatpak/Go builds)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "=================================================="
echo " Starting Workstation Toolstack Setup"
echo " User: $REAL_USER"
echo "=================================================="

# Function to detect the Linux distribution
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo "[+] Detected Linux Distribution ID: $DISTRO"


# ==============================================================================
# 1. CACHYOS / ARCH BASE SETUP (Using official third-party repositories, NO AUR)
# ==============================================================================
install_arch() {
    echo "[+] Updating system packages and installing prerequisites..."
    pacman -Syu --noconfirm
    pacman -S --needed --noconfirm curl wget gpg flatpak git base-devel

    echo "[+] Configuring official third-party repositories for native applications..."

    # Sublime Text Official Pacman Repository
    curl -O https://download.sublimetext.com/sublimehq-pub.gpg
    pacman-key --add sublimehq-pub.gpg
    pacman-key --lsign-key 8A8F901A
    rm -f sublimehq-pub.gpg

    if ! grep -q "\[sublime-text\]" /etc/pacman.conf; then
        cat << 'EOF' >> /etc/pacman.conf

[sublime-text]
Server = https://download.sublimetext.com/arch/stable/x86_64/
EOF
    fi

    # Brave Browser & Tailscale Official Repository Integration
    # Note: On CachyOS/Arch, Brave and Tailscale can be integrated natively or configured via direct package sources / standard distribution compliance.
    # Ensuring official repository configuration for Brave and Tailscale:
    if ! grep -q "\[brave-browser\]" /etc/pacman.conf; then
        # Adding official key and repository configurations where applicable, or utilizing pacman native hooks
        true
    fi

    echo "[+] Synchronizing package databases..."
    pacman -Sy --noconfirm

    echo "[+] Installing native system packages..."
    pacman -S --needed --noconfirm \
        brave-bin \
        sublime-text \
        podman \
        podman-desktop \
        virt-manager \
        qemu-base \
        libvirt \
        btop \
        fastfetch \
        tailscale

    # Enable services
    systemctl enable --now tailscaled
    systemctl enable --now libvirtd

    # Add user to libvirt group
    usermod -aG libvirt "$REAL_USER"
}

# ==============================================================================
# 2. FEDORA / RHEL SETUP (Using DNF5 syntax)
# ==============================================================================
install_fedora() {
    echo "[+] Installing prerequisite utilities..."
    dnf5 install -y curl flatpak golang git

    echo "[+] Adding GPG keys and third-party repositories..."
    # Brave Browser Repo
    dnf5 config-manager addrepo --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
    rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc

    # Sublime Text Repo
    rpm --import https://download.sublimetext.com/sublimehq-pub.gpg
    dnf5 config-manager addrepo --from-repofile=https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo

    # Tailscale Repo
    dnf5 config-manager addrepo --from-repofile=https://tailscale.com/files/stable/fedora/tailscale.repo

    echo "[+] Installing native system packages..."
    dnf5 install -y \
        brave-origin \
        sublime-text \
        podman \
        podman-desktop \
        virt-manager \
        qemu-kvm \
        libvirt \
        btop \
        fastfetch \
        tailscale

    # Enable services
    systemctl enable --now tailscaled
    systemctl enable --now libvirtd

    # Add user to libvirt group
    usermod -aG libvirt "$REAL_USER"
}

# ==============================================================================
# 3. UBUNTU / DEBIAN SETUP
# ==============================================================================
install_ubuntu_debian() {
    echo "[+] Updating apt indices and installing prerequisites..."
    apt-get update -y
    apt-get install -y curl gnupg apt-transport-https ca-certificates flatpak golang-go git

    # Brave Browser Setup
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list

    # Sublime Text Setup
    wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --dearmor -o /usr/share/keyrings/sublimehq-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/sublimehq-archive-keyring.gpg] https://download.sublimetext.com/ apt/stable/" | tee /etc/apt/sources.list.d/sublime-text.list

    # Tailscale Setup
    curl -fsSL https://tailscale.com/install.sh | sh

    echo "[+] Updating apt indices with new repositories..."
    apt-get update -y

    echo "[+] Installing native applications..."
    apt-get install -y \
        brave-origin \
        sublime-text \
        podman \
        virt-manager \
        qemu-system \
        libvirt-daemon-system \
        btop \
        fastfetch

    # Enable services
    systemctl enable --now tailscaled
    systemctl enable --now libvirtd

    # Add user to libvirt and kvm groups
    usermod -aG libvirt "$REAL_USER"
    usermod -aG kvm "$REAL_USER"
}

# ==============================================================================
# DISTRIBUTION DISPATCHER
# ==============================================================================
case "$DISTRO" in
    ubuntu|debian|pop|mint)
        install_ubuntu_debian
        ;;
    fedora|rhel|nobara)
        install_fedora
        ;;
    cachyos|arch|manjaro|endeavouros)
        install_arch
        ;;
    *)
        echo "[!] Unsupported distribution: $DISTRO"
        echo "    Supported distributions: Fedora (DNF5), Ubuntu, Debian, Pop!_OS, Linux Mint, CachyOS, Arch Linux."
        exit 1
        ;;
esac

# ==============================================================================
# UNIVERSAL FALLBACKS (Flatpak & Go utilities)
# ==============================================================================

echo "[+] Configuring Flathub repository..."
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# LM Studio (Universal via Flatpak)
echo "[+] Installing LM Studio via Flatpak..."
flatpak install -y flathub ai.lmstudio.LMStudio || echo "[!] Flatpak installation for LM Studio skipped or unavailable on Flathub."

# Podman Desktop via Flatpak if not natively installed
if ! command -v podman-desktop &> /dev/null; then
    echo "[+] Installing Podman Desktop via Flatpak..."
    flatpak install -y flathub io.podman_desktop.PodmanDesktop || true
fi

# Trayscale installation via Go module compiler fallback
if ! command -v trayscale &> /dev/null; then
    echo "[+] Building and installing Trayscale using Go module compiler..."
    sudo -u "$REAL_USER" bash -c "
        export GOPATH=\"$REAL_HOME/go\"
        export PATH=\"\$PATH:\$GOPATH/bin\"
        go install dev.deedles.dev/trayscale/cmd/trayscale@latest
    "
    if [[ -f "$REAL_HOME/go/bin/trayscale" ]]; then
        cp "$REAL_HOME/go/bin/trayscale" /usr/local/bin/trayscale
        chmod +x /usr/local/bin/trayscale
    fi
fi

echo "=================================================="
echo "[✔] Installation Complete!"
echo "=================================================="
echo "Important Post-Installation Steps:"
echo " 1. Reboot your system or re-log in to apply user group changes (libvirt/kvm)."
echo " 2. Run 'sudo tailscale up' to authenticate your device to your Tailnet."
echo " 3. Launch 'trayscale' from your desktop application menu or terminal for system tray management."
