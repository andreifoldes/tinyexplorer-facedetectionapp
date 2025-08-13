#!/bin/bash
# Setup script for dual Python environments in development mode

set -e

echo "Setting up dual Python environments for development..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not installed or not in PATH"
    echo "Please install Anaconda or Miniconda first"
    exit 1
fi

# Create YOLO environment
echo "Creating YOLO environment..."
if conda env list | grep -q "electron-python-yolo"; then
    echo "YOLO environment already exists, updating..."
    conda env update -f environment-yolo.yml
else
    echo "Creating new YOLO environment..."
    conda env create -f environment-yolo.yml
fi

# Create RetinaFace environment
echo "Creating RetinaFace environment..."
if conda env list | grep -q "electron-python-retinaface"; then
    echo "RetinaFace environment already exists, updating..."
    conda env update -f environment-retinaface.yml
else
    echo "Creating new RetinaFace environment..."
    conda env create -f environment-retinaface.yml
fi

echo "✅ Dual environment setup complete!"
echo ""
echo "Available environments:"
echo "- electron-python-yolo (for YOLO models)"
echo "- electron-python-retinaface (for RetinaFace models)"
echo ""
echo "The app will automatically switch between environments based on model selection."