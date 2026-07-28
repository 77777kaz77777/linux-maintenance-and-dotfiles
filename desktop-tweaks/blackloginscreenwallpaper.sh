#!/bin/bash

# Ensure the script is run with sudo
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit
fi

echo "Step 1: Creating GDM dconf profile..."
mkdir -p /etc/dconf/profile
cat <<EOF > /etc/dconf/profile/gdm
user-db:user
system-db:gdm
file-db:/usr/share/gdm/greeter-dconf-defaults
EOF

echo "Step 2: Creating black background configuration..."
mkdir -p /etc/dconf/db/gdm.d
cat <<EOF > /etc/dconf/db/gdm.d/10-black-bg
[com/ubuntu/login-screen]
background-color='#000000'
EOF

echo "Step 3: Updating dconf database..."
dconf update

echo "------------------------------------------------"
echo "Done! Please log out or restart to see changes."
echo "------------------------------------------------"
