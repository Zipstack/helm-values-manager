#!/bin/bash
set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
INSTALL_SOURCE="local"
GITHUB_URL="https://github.com/Zipstack/helm-values-manager"  # Correct capitalization
DEBUG_FLAG=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            if [[ "$2" != "local" && "$2" != "github" ]]; then
                echo "Error: --source must be either 'local' or 'github'"
                exit 1
            fi
            INSTALL_SOURCE="$2"
            shift 2
            ;;
        --github-url)
            # Remove .git suffix if present
            GITHUB_URL="${2%.git}"
            shift 2
            ;;
        --debug)
            DEBUG_FLAG="--debug"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--source local|github] [--github-url URL] [--debug]"
            echo "Example:"
            echo "  $0                                          # Install from local directory"
            echo "  $0 --source github                         # Install from default GitHub repo"
            echo "  $0 --source github --github-url URL        # Install from custom GitHub repo"
            echo "  $0 --debug                                # Run with debug output"
            exit 1
            ;;
    esac
done

# Get the absolute path to the plugin directory if installing locally
if [ "$INSTALL_SOURCE" = "local" ]; then
    PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

echo "Installing helm-values-manager plugin..."
# Remove existing plugin if it exists
helm plugin remove values-manager 2>/dev/null || true

# Install plugin based on source
if [ "$INSTALL_SOURCE" = "local" ]; then
    echo "Installing from local directory: $PLUGIN_DIR"
    helm plugin install "$PLUGIN_DIR"
else
    echo "Installing from GitHub: $GITHUB_URL"
    helm plugin install "$GITHUB_URL"
fi

echo -e "\n${GREEN}Running test sequence...${NC}"

# Clean up any existing test files
rm -f helm-values.json .helm-values.lock

# Initialize with a valid release name
echo -e "\n${GREEN}1. Initializing helm values configuration...${NC}"
helm values-manager init -r "test-release" $DEBUG_FLAG

# Add deployments
echo -e "\n${GREEN}2. Adding deployments...${NC}"
helm values-manager add-deployment test-deployment $DEBUG_FLAG
helm values-manager add-deployment dev $DEBUG_FLAG
helm values-manager add-deployment prod $DEBUG_FLAG

# Add value configurations
echo -e "\n${GREEN}3. Adding value configurations...${NC}"
helm values-manager add-value-config -p "app.config.name" -d "Application name" -r $DEBUG_FLAG
helm values-manager add-value-config -p "app.config.replicas" -d "Number of replicas" $DEBUG_FLAG

# Set values for different environments
echo -e "\n${GREEN}4. Setting values...${NC}"
helm values-manager set-value -p "app.config.name" -v "my-test-app" -d dev $DEBUG_FLAG
helm values-manager set-value -p "app.config.replicas" -v "1" -d dev $DEBUG_FLAG
helm values-manager set-value -p "app.config.name" -v "my-prod-app" -d prod $DEBUG_FLAG
helm values-manager set-value -p "app.config.replicas" -v "3" -d prod $DEBUG_FLAG

# Verify configurations
echo -e "\n${GREEN}5. Verifying configurations...${NC}"
echo -e "\nhelm-values.json contents:"
cat helm-values.json

echo -e "\n.helm-values.lock contents:"
cat .helm-values.lock

echo -e "\n${GREEN}Test sequence completed successfully!${NC}"
