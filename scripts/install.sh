#!/bin/bash
set -e

# Check if Python 3.7+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info[0] * 10 + sys.version_info[1])')
if [ "$PYTHON_VERSION" -lt 37 ]; then
    echo "Error: Python 3.7 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$HELM_PLUGIN_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$HELM_PLUGIN_DIR/venv"
fi

# Upgrade pip and install package
echo "Installing dependencies..."
"$HELM_PLUGIN_DIR/venv/bin/pip" install --upgrade pip
"$HELM_PLUGIN_DIR/venv/bin/pip" install -e $HELM_PLUGIN_DIR || {
    echo "Error: Failed to install package dependencies"
    exit 1
}

echo "helm-values-manager plugin installed successfully"
