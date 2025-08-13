#!/bin/bash

# Script to fix "damaged app" error for downloaded TinyExplorer FaceDetectionApp
# This removes the quarantine attribute that macOS adds to downloaded files

APP_PATH="$HOME/Downloads/TinyExplorer FaceDetectionApp.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    exit 1
fi

echo "Removing quarantine attribute from: $APP_PATH"

# Remove all extended attributes including quarantine
xattr -cr "$APP_PATH"

# Check if quarantine was removed
if xattr -l "$APP_PATH" | grep -q "com.apple.quarantine"; then
    echo "Warning: Quarantine attribute still present"
    # Try alternative method
    xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
else
    echo "Successfully removed quarantine attribute"
fi

echo "App should now open without 'damaged' warning"
echo "You can now open the app normally"