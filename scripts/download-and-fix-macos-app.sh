#!/bin/bash

# Script to download and fix macOS app from GitHub Actions artifacts
# This combines downloading with removing quarantine attributes

set -e

# Configuration
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
REPO="your-org/your-repo"  # Update with your repository
WORKFLOW_NAME="CI"  # Update with your workflow name
ARTIFACT_NAME="macos-build"  # Update with your artifact name
DOWNLOAD_DIR="$HOME/Downloads"
APP_NAME="TinyExplorer FaceDetectionApp.app"

# Function to remove quarantine from app
fix_quarantine() {
    local app_path="$1"
    echo "Removing quarantine attribute from: $app_path"
    
    # Remove all extended attributes including quarantine
    xattr -cr "$app_path"
    
    # Verify removal
    if xattr -l "$app_path" | grep -q "com.apple.quarantine"; then
        echo "Warning: Quarantine attribute still present, trying alternative method"
        xattr -d com.apple.quarantine "$app_path" 2>/dev/null
    else
        echo "Successfully removed quarantine attribute"
    fi
}

# Function to download latest artifact
download_artifact() {
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Error: GITHUB_TOKEN environment variable not set"
        echo "Set it with: export GITHUB_TOKEN=your_token"
        exit 1
    fi
    
    echo "Fetching latest successful workflow run..."
    
    # Get latest successful workflow run
    WORKFLOW_RUN=$(curl -s \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/workflows/$WORKFLOW_NAME/runs?status=success&per_page=1" \
        | jq -r '.workflow_runs[0].id')
    
    if [ "$WORKFLOW_RUN" = "null" ] || [ -z "$WORKFLOW_RUN" ]; then
        echo "Error: No successful workflow runs found"
        exit 1
    fi
    
    echo "Found workflow run: $WORKFLOW_RUN"
    
    # Get artifact URL
    ARTIFACT_URL=$(curl -s \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/runs/$WORKFLOW_RUN/artifacts" \
        | jq -r ".artifacts[] | select(.name==\"$ARTIFACT_NAME\") | .archive_download_url")
    
    if [ -z "$ARTIFACT_URL" ]; then
        echo "Error: Artifact '$ARTIFACT_NAME' not found"
        exit 1
    fi
    
    # Download artifact
    echo "Downloading artifact..."
    curl -L \
        -H "Authorization: token $GITHUB_TOKEN" \
        -o "$DOWNLOAD_DIR/artifact.zip" \
        "$ARTIFACT_URL"
    
    # Extract artifact
    echo "Extracting artifact..."
    cd "$DOWNLOAD_DIR"
    unzip -q -o artifact.zip
    rm artifact.zip
    
    echo "Downloaded to: $DOWNLOAD_DIR/$APP_NAME"
}

# Main execution
main() {
    # Download if GitHub token is provided
    if [ -n "$GITHUB_TOKEN" ]; then
        download_artifact
    fi
    
    # Check if app exists
    APP_PATH="$DOWNLOAD_DIR/$APP_NAME"
    if [ ! -d "$APP_PATH" ]; then
        echo "Error: App not found at $APP_PATH"
        echo "Please download the app first or provide GITHUB_TOKEN"
        exit 1
    fi
    
    # Fix quarantine
    fix_quarantine "$APP_PATH"
    
    echo ""
    echo "App is ready to use at: $APP_PATH"
    echo "You can now open it without security warnings"
}

main "$@"