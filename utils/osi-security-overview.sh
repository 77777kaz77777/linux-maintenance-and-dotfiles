#!/bin/bash
# Custom utility tool: OSI Layer Security Overview
# Displays the 7 OSI Layers alongside standard protocols and targeted security threats.

cat << 'EOF'
===================================================================
            OSI MODEL: PROTOCOLS & SECURITY THREATS
===================================================================

Layer 7: Application Layer
---------------------------
* Protocols: HTTP/HTTPS, FTP, SMTP, DNS, SSH, Telnet
* Threats:   SQL Injection (SQLi), Cross-Site Scripting (XSS), CSRF,
             Buffer Overflows, Command Injection, DNS Poisoning

Layer 6: Presentation Layer
---------------------------
* Protocols: SSL/TLS, MIME, JPEG, ASCII
* Threats:   SSL Stripping, Padding Oracle Attacks, Data Compression 
             Exploits, Malicious Payload Formatting

Layer 5: Session Layer
---------------------------
* Protocols: NetBIOS, RPC, PPTP, SOCKS
* Threats:   Session Hijacking, Session Replay, Session Fixation, 
             Man-in-the-Middle (MitM) Session Interception

Layer 4: Transport Layer
---------------------------
* Protocols: TCP, UDP, SCTP
* Threats:   SYN Flood, Port Scanning, TCP Spoofing/Reset Attacks, 
             UDP Flooding, Segmentation/Fragmentation Attacks

Layer 3: Network Layer
---------------------------
* Protocols: IP (IPv4/IPv6), ICMP, RIP, OSPF, BGP
* Threats:   IP Spoofing, ICMP Floods (Smurf Attack), DDoS Routing 
             Hijacks, BGP Route Poisoning

Layer 2: Data Link Layer
---------------------------
* Protocols: Ethernet (802.3 MAC), Wi-Fi (802.11 MAC), PPP, HDLC, VLAN (802.1Q)
* Threats:   ARP Spoofing, MAC Flooding, MAC Spoofing, VLAN Hopping, 
             STP Manipulation

Layer 1: Physical Layer
---------------------------
* Protocols: Ethernet (PHY), Wi-Fi (RF/PHY), DSL, Optical Fiber
* Threats:   Cable Tampering, Signal Jamming, Wiretapping/Eavesdropping, 
             Physical Rogue Devices
===================================================================
EOF
