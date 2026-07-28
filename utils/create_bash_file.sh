#!/bin/bash

# Get the desired filename from the user
read -p "Enter the desired filename (without .sh extension): " filename

# Check if the filename is empty
if [[ -z "$filename" ]]; then
  echo "Error: Filename cannot be empty."
  exit 1
fi

# Append .sh extension to the filename
filename="${filename}.sh"

# Check if the filename already exists
if [[ -f "$filename" ]]; then
  read -p "File '$filename' already exists. Overwrite? (y/N): " overwrite
  if [[ "$overwrite" =~ ^[yY]$ ]]; then
    echo "Overwriting file..."
  else
    echo "Exiting."
    exit 1
  fi
fi

# Create the empty bash file and add the shebang
echo "#!/bin/bash" > "$filename"

# Make the file executable
chmod +x "$filename"

# Print a success message
echo "File '$filename' created successfully."
