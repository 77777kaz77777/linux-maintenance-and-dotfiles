#!/usr/bin/env bash
# A interactive utility to easily toggle Tailscale on and off, with an optional prompt to route all traffic through a specific exit node
# Exit node domain
EXIT_NODE="yourdomain"

# Check status reliably
# Returns 0/Running if connected, non-zero or Stopped if down
STATUS_OUTPUT=$(tailscale status 2>&1)

if echo "$STATUS_OUTPUT" | grep -q "Tailscale is stopped"; then
    IS_RUNNING=false
elif tailscale status >/dev/null 2>&1; then
    IS_RUNNING=true
else
    IS_RUNNING=false
fi

if [ "$IS_RUNNING" = true ]; then
    echo "Tailscale is currently: ON"
    echo "---------------------------"
    read -rp "Do you want to turn Tailscale OFF? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Stopping Tailscale..."
        sudo tailscale down
        echo "Tailscale is now OFF."
    else
        echo "Leaving Tailscale ON."
    fi
else
    echo "Tailscale is currently: OFF"
    echo "---------------------------"
    read -rp "Do you want to turn Tailscale ON? (y/N): " response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        read -rp "Do you want to use exit node '$EXIT_NODE'? (y/N): " use_exit
        
        if [[ "$use_exit" =~ ^[Yy]$ ]]; then
            echo "Starting Tailscale with exit node..."
            sudo tailscale up --exit-node="$EXIT_NODE" --exit-node-allow-lan-access
        else
            echo "Starting Tailscale without exit node..."
            sudo tailscale up
        fi
        echo "Tailscale is now ON."
    else
        echo "Tailscale remains OFF."
    fi
fi
