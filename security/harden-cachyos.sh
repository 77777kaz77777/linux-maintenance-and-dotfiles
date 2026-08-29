#!/usr/bin/env bash
#Hardening script to apply firewall, AppArmor, and sysctl security tweaks on CachyOS.
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
echo "[1/6] Configuring Network Defense (UFW)..."

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
echo "[2/6] Setting up AppArmor and Security Profiles..."

pacman -S --needed --noconfirm apparmor apparmor.d

# Enable AppArmor parsing cache to speed up boot times
if [ -f /etc/apparmor/parser.conf ]; then
    sed -i 's/^#write-cache/write-cache/' /etc/apparmor/parser.conf
fi

systemctl enable apparmor.service

# ------------------------------------------------------------------------------
# 3. Kernel Command Line Configuration (AppArmor LSM Enablement)
# ------------------------------------------------------------------------------
echo "[3/6] Detecting Bootloader and Injecting AppArmor Parameters..."

LSM_PARAM="lsm=landlock,lockdown,yama,integrity,apparmor,bpf"

# --- CASE A: LIMINE BOOTLOADER (CachyOS Default) ---
if [ -f /etc/default/limine ]; then
    echo "[+] Limine configuration found at /etc/default/limine."
    
    if ! grep -q "apparmor" /etc/default/limine; then
        # Append LSM_PARAM to ALL KERNEL_CMDLINE instances inside /etc/default/limine
        sed -i "s/\(KERNEL_CMDLINE.*=\"[^\"]*\)/\1 ${LSM_PARAM}/g" /etc/default/limine
        echo "[+] Updated /etc/default/limine with AppArmor LSM parameters."
    else
        echo "[*] AppArmor parameter already present in /etc/default/limine."
    fi

    echo "[+] Regenerating initramfs and Limine boot entries..."
    mkinitcpio -P

# --- CASE B: SYSTEMD-BOOT ---
elif [ -f /etc/sdboot-manage.conf ]; then
    echo "[+] systemd-boot configuration found at /etc/sdboot-manage.conf."
    
    if ! grep -q "apparmor" /etc/sdboot-manage.conf; then
        sed -i "s/\(LINUX_OPTIONS=\"[^\"]*\)/\1 ${LSM_PARAM}/" /etc/sdboot-manage.conf
        echo "[+] Updated /etc/sdboot-manage.conf."
        sdboot-manage gen
    else
        echo "[*] AppArmor parameter already present in /etc/sdboot-manage.conf."
    fi

# --- CASE C: GRUB BOOTLOADER ---
elif [ -f /etc/default/grub ]; then
    echo "[+] GRUB configuration found at /etc/default/grub."
    
    if ! grep -q "apparmor" /etc/default/grub; then
        sed -i "s/\(GRUB_CMDLINE_LINUX_DEFAULT=\"[^\"]*\)/\1 ${LSM_PARAM}/" /etc/default/grub
        echo "[+] Updated /etc/default/grub."
        grub-mkconfig -o /boot/grub/grub.cfg
    else
        echo "[*] AppArmor parameter already present in /etc/default/grub."
    fi

else
    echo "[!] Warning: No standard bootloader config detected in /etc/default/."
fi

# Direct fallback check: If /boot/limine.conf exists, ensure cmdline includes lsm
if [ -f /boot/limine.conf ] && ! grep -q "apparmor" /boot/limine.conf; then
    echo "[+] Directly injecting AppArmor flag into /boot/limine.conf fallback..."
    sed -i "s/\(cmdline:.*\)/\1 ${LSM_PARAM}/g" /boot/limine.conf
fi

# ------------------------------------------------------------------------------
# 4. Kernel Parameter Hardening (Sysctl)
# ------------------------------------------------------------------------------
echo "[4/6] Applying Hardened Sysctl Rules..."

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
# 5. SSH Daemon Hardening (If Installed)
# ------------------------------------------------------------------------------
echo "[5/6] Checking and Hardening SSH Configuration..."

if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#\?MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
    echo "[+] SSH configuration hardened."
else
    echo "[*] OpenSSH server not installed, skipping SSH file changes."
fi

# ------------------------------------------------------------------------------
# 6. Lock Down Temporary Filesystems (/tmp)
# ------------------------------------------------------------------------------
echo "[6/6] Securing /tmp mount options..."

if ! grep -q "tmpfs /tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,mode=1777 0 0" >> /etc/fstab
    echo "[+] Secured /tmp mount point added to /etc/fstab."
else
    echo "[*] /tmp is already configured in /etc/fstab."
fi

# ------------------------------------------------------------------------------
# Verification
# ------------------------------------------------------------------------------
echo "=================================================="
echo " Setup Completed Successfully! "
echo "=================================================="
echo "Reboot your machine now:"
