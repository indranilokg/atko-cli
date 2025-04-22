#!/bin/bash

# Create man directory if it doesn't exist
sudo mkdir -p /usr/local/share/man/man1

# Install the man page
sudo cp atko.1 /usr/local/share/man/man1/

# On macOS, we don't need to run mandb
echo "Man page installed successfully. You can now view it with 'man atko'" 