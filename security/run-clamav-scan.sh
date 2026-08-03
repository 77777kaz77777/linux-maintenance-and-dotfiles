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
echo "              Scan Complete              "
echo "========================================="
