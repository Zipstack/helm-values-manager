#!/bin/bash

set -e

# Get the directory where the plugin is installed
PLUGIN_DIR="$HELM_PLUGIN_DIR"
if [ -z "$PLUGIN_DIR" ]; then
    PLUGIN_DIR="$(dirname "$0")"
fi

cd "$PLUGIN_DIR"

# Create bin directory if it doesn't exist
mkdir -p bin

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment and install dependencies using uv
echo "Creating virtual environment and installing dependencies..."
uv venv .venv
uv pip install -e .

# Create the executable wrapper
cat > bin/helm-values-manager << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment and run the Python module
source "$PLUGIN_DIR/.venv/bin/activate"
python -m helm_values_manager.cli "$@"
EOF

# Make the wrapper executable
chmod +x bin/helm-values-manager

echo "helm-values-manager plugin installed successfully!"