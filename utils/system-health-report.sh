#!/usr/bin/env bash
# Description: Generates a quick diagnostic report of system health, disk usage, and failed systemd services.

# Enforce strict error handling
set -euo pipefail

echo "=================================================="
echo "           SYSTEM HEALTH REPORT                   "
echo "           Date: $(date "+%Y-%m-%d %H:%M:%S")     "
echo "           Hostname: $(hostname)                  "
echo "=================================================="
echo ""

# 1. Check Uptime and CPU Load Average
# The load averages represent 1, 5, and 15 minute intervals.
echo "[+] Uptime & CPU Load Average:"
uptime
echo ""

# 2. Check Memory & Swap Usage
# -h provides human-readable output (MB/GB).
echo "[+] Memory Usage:"
free -h
echo ""

# 3. Check Disk Space
# -h: Human readable
# -T: Print file system type
# -x: Exclude temporary and loop/snap/flatpak filesystems for a cleaner output
echo "[+] Real Disk Space Usage:"
df -h -T -x tmpfs -x devtmpfs -x squashfs -x efivarfs
echo ""

# 4. Check for Disk Space Warnings (>85% capacity)
echo "[+] Disk Capacity Warnings:"
warning_found=false
# Parse df output, grab usage percentage and mount point, skipping the header line
while read -r usage mount; do
    # Remove the % sign for integer comparison
    usage_val=${usage%\%}
    if [ "$usage_val" -gt 85 ]; then
        echo "    ⚠️  WARNING: Partition '$mount' is at ${usage} capacity!"
        warning_found=true
    fi
done < <(df -h -T -x tmpfs -x devtmpfs -x squashfs -x efivarfs | awk 'NR>1 {print $6, $7}')

if [ "$warning_found" = false ]; then
    echo "    ✅ No partitions are above 85% capacity."
fi
echo ""

# 5. Check for Failed Systemd Services
echo "[+] Failed Systemd Services:"
# --failed limits output to failed units
# --no-legend suppresses header and footer lines
# --plain suppresses the circle indicators for easier text parsing
failed_services=$(systemctl --failed --no-legend --plain)

if [ -z "$failed_services" ]; then
    echo "    ✅ No failed systemd services. System is running cleanly."
else
    echo "    ❌ WARNING: The following services have failed:"
    echo "$failed_services"
fi
echo ""
echo "=================================================="
echo "                 REPORT COMPLETE                  "
echo "=================================================="
