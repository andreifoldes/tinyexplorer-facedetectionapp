#!/bin/bash
# Wrapper script to launch AppImage with proper flags for GUI environments

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the AppImage in the dist directory
APPIMAGE_FILE=$(find "$SCRIPT_DIR/dist" -name "*.AppImage" -type f | head -n 1)

if [ -z "$APPIMAGE_FILE" ]; then
    echo "Error: No AppImage found in $SCRIPT_DIR/dist"
    exit 1
fi

echo "Launching: $APPIMAGE_FILE"

# Launch AppImage with necessary flags for Linux compatibility
# --no-sandbox: Required for systems where user namespaces are disabled
# --disable-dev-shm-usage: Helps with /dev/shm issues in containers/restricted environments
exec "$APPIMAGE_FILE" --no-sandbox --disable-dev-shm-usage "$@"