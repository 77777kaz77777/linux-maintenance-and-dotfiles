#!/bin/bash
# Custom reference utility that provides a breakdown of security at each OSI layer.
# Displays the 7 OSI Layers alongside standard protocols and targeted security threats.

# ANSI Color Codes
RESET='\033[0m'
BOLD='\033[1m'
CYAN='\033[36m'
BLUE='\033[34m'
GREEN='\033[32m'
RED='\033[31m'

echo -e "${BOLD}${CYAN}===================================================================${RESET}"
echo -e "${BOLD}${CYAN}               OSI MODEL: PROTOCOLS & SECURITY THREATS${RESET}"
echo -e "${BOLD}${CYAN}===================================================================${RESET}\n"

# Function to cleanly format and print each layer
print_layer() {
    local layer="$1"
    local protocols="$2"
    local threats="$3"

    echo -e "${BOLD}${BLUE}${layer}${RESET}"
    echo -e "---------------------------"
    echo -e "${BOLD}${GREEN}* Protocols:${RESET}${protocols}"
    echo -e "${BOLD}${RED}* Threats:  ${RESET}${threats}\n"
}

print_layer "Layer 7: Application Layer" \
  "HTTP/HTTPS, FTP, SMTP, DNS, SSH, Telnet" \
  "SQL Injection (SQLi), Cross-Site Scripting (XSS), CSRF,\n             Buffer Overflows, Command Injection, DNS Poisoning"

print_layer "Layer 6: Presentation Layer" \
  "SSL/TLS, MIME, JPEG, ASCII" \
  "SSL Stripping, Padding Oracle Attacks, Data Compression\n             Exploits, Malicious Payload Formatting"

print_layer "Layer 5: Session Layer" \
  "NetBIOS, RPC, PPTP, SOCKS" \
  "Session Hijacking, Session Replay, Session Fixation,\n             Man-in-the-Middle (MitM) Session Interception"

print_layer "Layer 4: Transport Layer" \
  "TCP, UDP, SCTP" \
  "SYN Flood, Port Scanning, TCP Spoofing/Reset Attacks,\n             UDP Flooding, Segmentation/Fragmentation Attacks"

print_layer "Layer 3: Network Layer" \
  "IP (IPv4/IPv6), ICMP, RIP, OSPF, BGP" \
  "IP Spoofing, ICMP Floods (Smurf Attack), DDoS Routing\n             Hijacks, BGP Route Poisoning"

print_layer "Layer 2: Data Link Layer" \
  "Ethernet (802.3 MAC), Wi-Fi (802.11 MAC), PPP, HDLC, VLAN (802.1Q)" \
  "ARP Spoofing, MAC Flooding, MAC Spoofing, VLAN Hopping,\n             STP Manipulation"

print_layer "Layer 1: Physical Layer" \
  "Ethernet (PHY), Wi-Fi (RF/PHY), DSL, Optical Fiber" \
  "Cable Tampering, Signal Jamming, Wiretapping/Eavesdropping,\n             Physical Rogue Devices"

echo -e "${BOLD}${CYAN}===================================================================${RESET}"
