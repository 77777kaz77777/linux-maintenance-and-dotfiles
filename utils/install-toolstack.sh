#!/usr/bin/env bash
#is a work in progress and will have stuff added and removed 
# Exit on error, treat unset variables as an error, and fail on pipeline errors
set -euo pipefail

# Check for root / sudo privileges
if [[ $EUID -ne 0 ]]; then
   echo "[!] This script must be run with sudo or as root to configure software repositories and system packages."
   echo "    Usage: sudo bash $0"
   exit 1
fi

# Detect non-root real user for user-scoped operations (like Flatpak/Go builds)
# Chained fallbacks prevent 'unbound variable' errors in containers
REAL_USER="${SUDO_USER:-${USER:-$(id -un)}}"
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

# Function to safely add user to a group if not already a member
add_group() {
    local target_group=$1
    if ! getent group "$target_group" &>/dev/null; then
        echo "[!] Group $target_group does not exist (expected in some minimal containers). Skipping."
        return 0
    fi

    if ! id -nG "$REAL_USER" | grep -qw "$target_group"; then
        echo "[+] Adding $REAL_USER to $target_group group..."
        usermod -aG "$target_group" "$REAL_USER" || echo "[!] Failed to add user to $target_group."
    else
        echo "[=] User $REAL_USER is already in $target_group group, skipping."
    fi
}

# Function to safely enable services, bypassing if systemd is not active (containers)
enable_service() {
    local service_name=$1
    
    if [[ ! -d /run/systemd/system ]]; then
        echo "[=] Systemd is not running (container detected). Skipping $service_name enablement."
        return 0
    fi

    if ! systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        echo "[+] Enabling and starting $service_name..."
        systemctl enable --now "$service_name" || echo "[!] Failed to enable $service_name."
    else
        echo "[=] Service $service_name is already enabled, skipping."
    fi
}

# ==============================================================================
# 1. CACHYOS / ARCH BASE SETUP (Using official third-party repositories, NO AUR)
# ==============================================================================
install_arch() {
    echo "[+] Updating system packages and installing prerequisites..."
    pacman -Syu --noconfirm
    pacman -S --needed --noconfirm curl wget gpg flatpak git base-devel

    echo "[+] Configuring official third-party repositories for native applications..."

    # Sublime Text Official Pacman Repository
    if ! grep -q "\[sublime-text\]" /etc/pacman.conf; then
        echo "[+] Adding Sublime Text repository..."
        curl -O https://download.sublimetext.com/sublimehq-pub.gpg
        pacman-key --add sublimehq-pub.gpg
        pacman-key --lsign-key 8A8F901A
        rm -f sublimehq-pub.gpg
        cat << 'EOF' >> /etc/pacman.conf

[sublime-text]
Server = https://download.sublimetext.com/arch/stable/x86_64/
EOF
    else
        echo "[=] Sublime Text repository already configured, skipping."
    fi

    # Brave Browser & Tailscale Official Repository Integration
    if ! grep -q "\[brave-browser\]" /etc/pacman.conf; then
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

    enable_service tailscaled
    enable_service libvirtd
    add_group libvirt
}

# ==============================================================================
# 2. FEDORA / RHEL SETUP (Using DNF5 syntax)
# ==============================================================================
install_fedora() {
    echo "[+] Installing prerequisite utilities..."
    dnf5 install -y curl flatpak golang git

    echo "[+] Adding GPG keys and third-party repositories..."
    
    if [[ ! -f /etc/yum.repos.d/brave-browser.repo ]]; then
        echo "[+] Adding Brave Browser repository..."
        dnf5 config-manager addrepo --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
        rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc
    else
        echo "[=] Brave Browser repository already exists, skipping."
    fi

    if [[ ! -f /etc/yum.repos.d/sublime-text.repo ]]; then
        echo "[+] Adding Sublime Text repository..."
        rpm --import https://download.sublimetext.com/sublimehq-pub.gpg
        dnf5 config-manager addrepo --from-repofile=https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo
    else
        echo "[=] Sublime Text repository already exists, skipping."
    fi

    if [[ ! -f /etc/yum.repos.d/tailscale.repo ]]; then
        echo "[+] Adding Tailscale repository..."
        dnf5 config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo
    else
        echo "[=] Tailscale repository already exists, skipping."
    fi

    echo "[+] Installing native system packages..."
    dnf5 install -y \
        brave-origin \
        sublime-text \
        podman \
        virt-manager \
        qemu-kvm \
        libvirt \
        btop \
        fastfetch \
        tailscale

    enable_service tailscaled
    enable_service libvirtd
    add_group libvirt
}

# ==============================================================================
# 3. UBUNTU / DEBIAN SETUP
# ==============================================================================
install_ubuntu_debian() {
    echo "[+] Updating apt indices and installing prerequisites..."
    apt-get update -y
    apt-get install -y curl gnupg apt-transport-https ca-certificates flatpak golang-go git

    if [[ ! -f /etc/apt/sources.list.d/brave-browser-release.list ]]; then
        echo "[+] Adding Brave Browser repository..."
        curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list
    else
        echo "[=] Brave Browser repository already exists, skipping."
    fi

    if [[ ! -f /etc/apt/sources.list.d/sublime-text.list ]]; then
        echo "[+] Adding Sublime Text repository..."
        wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --yes --dearmor -o /usr/share/keyrings/sublimehq-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/sublimehq-archive-keyring.gpg] https://download.sublimetext.com/ apt/stable/" | tee /etc/apt/sources.list.d/sublime-text.list
    else
        echo "[=] Sublime Text repository already exists, skipping."
    fi

    if ! command -v tailscale &> /dev/null; then
        echo "[+] Installing Tailscale..."
        curl -fsSL https://tailscale.com/install.sh | sh
    else
        echo "[=] Tailscale already installed, skipping install script."
    fi

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

    enable_service tailscaled
    enable_service libvirtd
    add_group libvirt
    add_group kvm
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
# Added "|| true" to prevent namespace permission denials in containers from crashing the script
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo || true

# LM Studio (Universal via Flatpak)
if ! flatpak list 2>/dev/null | grep -qi "ai.lmstudio.LMStudio"; then
    echo "[+] Installing LM Studio via Flatpak..."
    flatpak install -y flathub ai.lmstudio.LMStudio || echo "[!] Flatpak installation for LM Studio skipped or unavailable in container context."
else
    echo "[=] LM Studio Flatpak already installed, skipping."
fi

# Podman Desktop via Flatpak if not natively installed
if ! command -v podman-desktop &> /dev/null; then
    if ! flatpak list 2>/dev/null | grep -qi "io.podman_desktop.PodmanDesktop"; then
        echo "[+] Installing Podman Desktop via Flatpak..."
        flatpak install -y flathub io.podman_desktop.PodmanDesktop || echo "[!] Flatpak installation for Podman Desktop skipped or unavailable in container context."
    else
        echo "[=] Podman Desktop Flatpak already installed, skipping."
    fi
else
    echo "[=] Podman Desktop native package already installed, skipping Flatpak fallback."
fi

# Trayscale installation via Go module compiler fallback
if ! command -v trayscale &> /dev/null; then
    echo "[+] Building and installing Trayscale using Go module compiler..."
    # If REAL_HOME is / (as it can be in some root container setups), adjust to avoid permission issues
    if [[ "$REAL_HOME" == "/" ]]; then
        REAL_HOME="/root"
    fi
    
    sudo -u "$REAL_USER" bash -c "
        export GOPATH=\"$REAL_HOME/go\"
        export PATH=\"\$PATH:\$GOPATH/bin\"
        go install dev.deedles.dev/trayscale/cmd/trayscale@latest
    "
    if [[ -f "$REAL_HOME/go/bin/trayscale" ]]; then
        cp "$REAL_HOME/go/bin/trayscale" /usr/local/bin/trayscale
        chmod +x /usr/local/bin/trayscale
    fi
else
    echo "[=] Trayscale already installed, skipping build."
fi

echo "=================================================="
echo "[✔] Installation Complete!"
echo "=================================================="
echo "Important Post-Installation Steps:"
echo " 1. Reboot your system or re-log in to apply user group changes (libvirt/kvm)."
echo " 2. Run 'sudo tailscale up' to authenticate your device to your Tailnet."
echo " 3. Launch 'trayscale' from your desktop application menu or terminal for system tray management."
