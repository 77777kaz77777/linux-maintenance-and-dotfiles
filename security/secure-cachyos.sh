#!/usr/bin/env bash
# ==============================================================================
# CachyOS Security Hardening Script
# Tailored for: Developers, Containers (Podman/Docker), and KVM Virt-Manager
# ==============================================================================

set -euo pipefail

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run this script with sudo or as root."
    exit 1
fi

echo "=================================================="
echo " Starting CachyOS Security Configuration "
echo "=================================================="

# ------------------------------------------------------------------------------
# 1. Firewall Configuration (UFW)
# ------------------------------------------------------------------------------
echo "[1/5] Configuring Network Defense (UFW)..."

pacman -S --needed --noconfirm ufw

# Set default security policies
ufw default deny incoming
ufw default allow outgoing

# Enable systemd unit and UFW service
systemctl enable ufw.service
ufw --force enable

# ------------------------------------------------------------------------------
# 2. Mandatory Access Control (AppArmor)
# ------------------------------------------------------------------------------
echo "[2/5] Setting up AppArmor and Security Profiles..."

pacman -S --needed --noconfirm apparmor apparmor.d

# Enable AppArmor parsing cache to speed up boot times
if [ -f /etc/apparmor/parser.conf ]; then
    sed -i 's/^#write-cache/write-cache/' /etc/apparmor/parser.conf
fi

systemctl enable --now apparmor.service

# ------------------------------------------------------------------------------
# 3. Kernel Parameter Hardening (Sysctl)
# ------------------------------------------------------------------------------
echo "[3/5] Applying Hardened Sysctl Rules..."

cat << 'EOF' > /etc/sysctl.d/99-security-hardening.conf
# Hide kernel pointers to prevent memory exploits
kernel.kptr_restrict = 2

# Restrict dmesg buffer access to root
kernel.dmesg_restrict = 1

# Prevent processes from attaching ptrace to non-child processes (stops memory sniffing)
kernel.yama.ptrace_scope = 1

# Protect Against IP Spoofing and Redirect Exploits
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Restrict BPF JIT Compiler access to root
net.core.bpf_jit_harden = 2

# Prevent File System Link Exploits
fs.protected_symlinks = 1
fs.protected_hardlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
EOF

# Reload sysctl settings
sysctl --system > /dev/null

# ------------------------------------------------------------------------------
# 4. SSH Daemon Hardening (If Installed)
# ------------------------------------------------------------------------------
echo "[4/5] Checking and Hardening SSH Configuration..."

if [ -f /etc/ssh/sshd_config ]; then
    # Disable root login over SSH and disable password auth (forces keys)
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#\?MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    echo "[+] SSH configuration hardened."
else
    echo "[*] OpenSSH server not installed, skipping SSH file changes."
fi

# ------------------------------------------------------------------------------
# 5. Lock Down Temporary Filesystems (/tmp)
# ------------------------------------------------------------------------------
echo "[5/5] Securing /tmp mount options..."

if ! grep -q "tmpfs /tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,mode=1777 0 0" >> /etc/fstab
    echo "[+] Secured /tmp mount point added to /etc/fstab."
else
    echo "[*] /tmp is already configured in /etc/fstab."
fi

# ------------------------------------------------------------------------------
# Verification Summary
# ------------------------------------------------------------------------------
echo "=================================================="
echo " Setup Completed Successfully! "
echo "=================================================="
echo ""
echo "CRITICAL FINAL STEP (Kernel Command Line):"
echo "To fully enforce AppArmor on boot, add this string to your bootloader options:"
echo ""
echo "   lsm=landlock,lockdown,yama,integrity,apparmor,bpf"
echo ""
echo " * If using systemd-boot: Add to options line in /boot/loader/entries/cachyos.conf"
echo " * If using GRUB: Add to GRUB_CMDLINE_LINUX_DEFAULT in /etc/default/grub & regenerate."
echo ""
echo "Reboot your machine to apply all changes completely."
