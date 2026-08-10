#!/bin/bash
# Sets terminal background to solid black (#000000), default text to pure white

set -euo pipefail

# 1. Apply immediate runtime change using standard OSC Escape Sequences and PS1 override
apply_runtime_colors() {
    # OSC 10: Set default text foreground color to White (#FFFFFF)
    printf '\033]10;#FFFFFF\007'
    
    # OSC 11: Set default background color to Black (#000000)
    printf '\033]11;#000000\007'
    
    # Override immediate subshell prompt variable to remove green ANSI escape codes
    export PS1='\u@\h:\w\$ '
    
    # Clear screen buffer to repaint the entire background canvas immediately
    clear
}

# 2. Generate and store a persistent KDE Konsole Color Scheme file
apply_persistent_scheme() {
    local scheme_dir="${HOME}/.local/share/konsole"
    local scheme_file="${scheme_dir}/PureWhiteOnBlack.colorscheme"

    # Ensure local Konsole user profile directory exists
    mkdir -p "${scheme_dir}"

    # Write standard INI-formatted Konsole color scheme
    cat << 'EOF' > "${scheme_file}"
[General]
Description=Pure White on Black
Opacity=1

[Background]
Color=0,0,0

[BackgroundFaint]
Color=0,0,0

[BackgroundIntense]
Color=0,0,0

[Foreground]
Color=255,255,255

[ForegroundFaint]
Color=200,200,200

[ForegroundIntense]
Color=255,255,255

[Color0]
Color=0,0,0

[Color0Intense]
Color=128,128,128

[Color7]
Color=220,220,220

[Color7Intense]
Color=255,255,255
EOF

    echo "Persistent color scheme created at: ${scheme_file}"

    # Update default profile if it exists in local storage
    local default_profile="${scheme_dir}/Profile 1.profile"
    if [[ -f "${default_profile}" ]]; then
        if grep -q "^ColorScheme=" "${default_profile}"; then
            sed -i 's/^ColorScheme=.*/ColorScheme=PureWhiteOnBlack/' "${default_profile}"
        else
            echo "ColorScheme=PureWhiteOnBlack" >> "${default_profile}"
        fi
        echo "Updated existing profile at: ${default_profile}"
    fi
}

# 3. Permanently update ~/.bashrc to ensure future interactive sessions use white text
update_bashrc_prompt() {
    local bashrc="${HOME}/.bashrc"
    local prompt_entry='export PS1="\u@\h:\w\$ "'

    if [[ -f "${bashrc}" ]]; then
        # Append the uncolored prompt declaration if not already present
        if ! grep -qF 'export PS1="\u@\h:\w\$ "' "${bashrc}"; then
            echo "" >> "${bashrc}"
            echo "# Override shell prompt to use default white text" >> "${bashrc}"
            echo "${prompt_entry}" >> "${bashrc}"
            echo "Updated ${bashrc} with white PS1 prompt definition."
        else
            echo "${bashrc} already contains the plain PS1 prompt override."
        fi
    fi
}

main() {
    apply_runtime_colors
    apply_persistent_scheme
    update_bashrc_prompt
    echo "Konsole color scheme and shell prompt updated successfully."
}

main "$@"
