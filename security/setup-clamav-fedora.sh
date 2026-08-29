#!/bin/bash
# Automated script to install and set up ClamAV on Fedora.

# Ensure the script is run with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "This setup script requires root privileges. Run with sudo."
  exit 1
fi

# Verify ClamAV is installed
echo "Checking for Fedora ClamAV packages..."
if ! command -v clamdscan >/dev/null 2>&1 || ! command -v freshclam >/dev/null 2>&1; then
  echo "Error: ClamAV utilities are not installed or not in your PATH."
  echo "Please install them via: sudo dnf install clamav clamav-freshclam clamd"
  exit 1
fi
echo "ClamAV is installed. Proceeding with Fedora configuration setup..."

# Configure SELinux to allow ClamAV to scan system and home directories
if command -v getenforce >/dev/null 2>&1 && [ "$(getenforce)" = "Enforcing" ]; then
  echo "SELinux is Enforcing. Enabling antivirus_can_scan_system boolean..."
  setsebool -P antivirus_can_scan_system 1
fi

# 1. Create the nightly multi-threaded scan script
echo "Creating nightly scan script at /usr/local/bin/clamav-nightly-scan.sh..."
cat << 'EOF' > /usr/local/bin/clamav-nightly-scan.sh
#!/bin/bash
LOGFILE="/var/log/clamav/daily_scan.log"
mkdir -p /var/log/clamav
echo "=== Scan Started: $(date) ===" >> "$LOGFILE"
clamdscan --fdpass --infected --multiscan --log="$LOGFILE" /home /usr/bin /usr/local/bin
echo "=== Scan Finished: $(date) ===" >> "$LOGFILE"
EOF
chmod +x /usr/local/bin/clamav-nightly-scan.sh

# 2. Create the systemd service unit
echo "Creating systemd service at /etc/systemd/system/clamav-nightly-scan.service..."
cat << 'EOF' > /etc/systemd/system/clamav-nightly-scan.service
[Unit]
Description=Trigger multi-threaded ClamAV system scan
After=clamd@scan.service

[Service]
Type=simple
ExecStart=/usr/local/bin/clamav-nightly-scan.sh
EOF

# 3. Create the systemd timer unit
echo "Creating systemd timer at /etc/systemd/system/clamav-nightly-scan.timer..."
cat << 'EOF' > /etc/systemd/system/clamav-nightly-scan.timer
[Unit]
Description=Run ClamAV Scan Automatically

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 4. Create the manual on-demand terminal scanner
echo "Creating manual scan script at /usr/local/bin/sys-scan..."
cat << 'EOF' > /usr/local/bin/sys-scan
#!/bin/bash
echo "========================================="
echo "    Starting Manual ClamAV System Scan   "
echo "========================================="
echo "Scanning: /home, /usr/bin, /usr/local/bin"
echo "Please wait..."
echo ""
clamdscan --fdpass --multiscan /home /usr/bin /usr/local/bin
echo ""
echo "========================================="
echo "             Scan Complete               "
echo "========================================="
EOF
chmod +x /usr/local/bin/sys-scan

# 5. Create the manual Freshclam signature updater
echo "Creating manual updater script at /usr/local/bin/clamsig..."
cat << 'EOF' > /usr/local/bin/clamsig
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "This script needs root privileges to stop/start systemd services."
  echo "Re-running script with sudo..."
  exec sudo "$0" "$@"
fi
echo "========================================="
echo "       Forcing ClamAV Signature Update   "
echo "========================================="
echo ""
echo "[1/3] Stopping clamav-freshclam service to release file locks..."
systemctl stop clamav-freshclam.service
echo "[2/3] Downloading latest malware definitions from Cisco Talos..."
echo "------------------------------------------------------------"
freshclam
echo "------------------------------------------------------------"
echo "[3/3] Restarting clamav-freshclam for automated background checks..."
systemctl start clamav-freshclam.service
echo ""
echo "========================================="
echo "       Update Sequence Complete!         "
echo "========================================="
EOF
chmod +x /usr/local/bin/clamsig

# 6. Reload systemd daemon and activate the timer
echo "Reloading systemd daemon to recognize new units..."
systemctl daemon-reload
echo "Enabling and starting clamav-nightly-scan.timer..."
systemctl enable clamav-nightly-scan.timer
systemctl start clamav-nightly-scan.timer

echo "========================================="
echo "Fedora Setup complete! The following system-wide commands are available:"
echo "1. sys-scan (Run a manual scan)"
echo "2. clamsig (Force virus definitions update)"
echo "Note: The nightly scan will trigger automatically via systemd at 2:00 AM."
echo "========================================="
