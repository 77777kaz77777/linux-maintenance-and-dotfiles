#!/bin/bash
# Description: Interactive generator that creates an executable Bash script with standard headers and strict error flags.


set -euo pipefail

# Prompt user for the filename
read -rp "Enter desired script name (e.g. system-cleanup): " raw_filename

# Check if input is empty
if [[ -z "${raw_filename// /}" ]]; then
  echo "Error: Filename cannot be empty or whitespace." >&2
  exit 1
fi

# Strip .sh extension if typed by user, then re-append cleanly
base_name="${raw_filename%.sh}"
filename="${base_name}.sh"

# Check if the file already exists
if [[ -f "$filename" ]]; then
  read -rp "File '$filename' already exists. Overwrite? (y/N): " overwrite
  if [[ ! "$overwrite" =~ ^[yY]$ ]]; then
    echo "Operation canceled. Exiting."
    exit 0
  fi
fi

# Write shebang and production-grade script header
cat <<'EOF' > "$filename"
#!/bin/bash
# ==============================================================================
# Script Name: 
# Description: 
# ==============================================================================

# Exit immediately on error, unset variable, or piped command failure
set -euo pipefail

# Require root privileges (Uncomment if needed)
# if [[ $EUID -ne 0 ]]; then
#   echo "Error: This script must be run as root or via sudo." >&2
#   exit 1
# fi

EOF

# Make the new script executable
chmod +x "$filename"

echo "--------------------------------------------------"
echo "Success: Created executable script '$filename'"
echo "Path: $(pwd)/$filename"
echo "--------------------------------------------------"
