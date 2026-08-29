# Multi-threaded ClamAV scan script designed to run nightly.
#!/bin/bash
LOGFILE="/var/log/clamav/daily_scan.log"

# Create log folder if missing
mkdir -p /var/log/clamav

echo "=== Scan Started: $(date) ===" >> "$LOGFILE"
clamdscan --fdpass --infected --multiscan --log="$LOGFILE" /home /usr/bin /usr/local/bin
echo "=== Scan Finished: $(date) ===" >> "$LOGFILE"
