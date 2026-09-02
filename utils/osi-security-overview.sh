#!/bin/bash
# Custom reference utility that provides a breakdown of security at each OSI layer.
# Displays the 7 OSI Layers alongside standard protocols and targeted security threats.

# ANSI Color & Formatting Codes
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[1;36m'
GREEN='\033[1;32m'
RED='\033[1;31m'
MAGENTA='\033[1;35m'
WHITE='\033[1;37m'

echo -e "\n${BOLD}${MAGENTA} ╔═══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${MAGENTA} ║           ${CYAN}OSI MODEL: PROTOCOLS & SECURITY THREATS${MAGENTA}         ║${RESET}"
echo -e "${BOLD}${MAGENTA} ╚═══════════════════════════════════════════════════════════╝${RESET}\n"

# Function to cleanly format and print each layer in a tree structure
print_layer() {
    local layer="$1"
    local protocols="$2"
    local threats_line1="$3"
    local threats_line2="$4"

    echo -e "${BOLD}${CYAN}■ ${layer}${RESET}"
    echo -e "${DIM}│${RESET}"
    echo -e "${DIM}├─${RESET} ${BOLD}${GREEN}[+] Protocols:${RESET}  ${protocols}"
    
    if [ -n "$threats_line2" ]; then
        echo -e "${DIM}└─${RESET} ${BOLD}${RED}[!] Threats:  ${RESET}  ${threats_line1}"
        echo -e "                  ${threats_line2}\n"
    else
        echo -e "${DIM}└─${RESET} ${BOLD}${RED}[!] Threats:  ${RESET}  ${threats_line1}\n"
    fi
}

print_layer "Layer 7: Application Layer" \
  "HTTP/HTTPS, FTP, SMTP, DNS, SSH, Telnet" \
  "SQL Injection (SQLi), Cross-Site Scripting (XSS), CSRF," \
  "Buffer Overflows, Command Injection, DNS Poisoning"

print_layer "Layer 6: Presentation Layer" \
  "SSL/TLS, MIME, JPEG, ASCII" \
  "SSL Stripping, Padding Oracle Attacks," \
  "Data Compression Exploits, Malicious Payload Formatting"

print_layer "Layer 5: Session Layer" \
  "NetBIOS, RPC, PPTP, SOCKS" \
  "Session Hijacking, Session Replay, Session Fixation," \
  "Man-in-the-Middle (MitM) Session Interception"

print_layer "Layer 4: Transport Layer" \
  "TCP, UDP, SCTP" \
  "SYN Flood, Port Scanning, TCP Spoofing/Reset Attacks," \
  "UDP Flooding, TCP Segmentation Attacks"

print_layer "Layer 3: Network Layer" \
  "IP (IPv4/IPv6), ICMP, IPSec, RIP, OSPF, BGP" \
  "IP Spoofing, ICMP Floods (Smurf Attack), DDoS Routing Hijacks," \
  "BGP Route Poisoning, IP Fragmentation Attacks"

print_layer "Layer 2: Data Link Layer" \
  "Ethernet (802.3 MAC), Wi-Fi (802.11 MAC), PPP, HDLC, VLAN (802.1Q)" \
  "ARP Spoofing, MAC Flooding, MAC Spoofing, VLAN Hopping," \
  "STP Manipulation"

print_layer "Layer 1: Physical Layer" \
  "Ethernet (PHY), Wi-Fi (RF/PHY), DSL, Optical Fiber" \
  "Cable Tampering, Signal Jamming, Wiretapping/Eavesdropping," \
  "Physical Rogue Devices"
