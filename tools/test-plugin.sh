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
CLEANUP_ONLY=false

# Function to clean up test files and optionally uninstall plugin
cleanup() {
    echo -e "\n${GREEN}Cleaning up test files...${NC}"

    # Remove test files
    rm -f helm-values.json .helm-values.lock
    rm -f *.values.yaml
    rm -rf output

    # Always uninstall the plugin
    echo "Removing helm-values-manager plugin..."
    helm plugin remove values-manager 2>/dev/null || true

    echo -e "${GREEN}Cleanup complete.${NC}"
}

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
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--source local|github] [--github-url URL] [--debug] [--cleanup]"
            echo "Options:"
            echo "  --source local|github    Source to install plugin from (default: local)"
            echo "  --github-url URL         GitHub URL to install plugin from"
            echo "  --debug                  Run with debug output"
            echo "  --cleanup                Only clean up test files and uninstall plugin"
            echo "Examples:"
            echo "  $0                       # Install from local directory and run tests"
            echo "  $0 --source github       # Install from default GitHub repo and run tests"
            echo "  $0 --cleanup             # Only clean up test files and uninstall plugin"
            exit 1
            ;;
    esac
done

# Clean up any existing test files
cleanup

# If cleanup only, just exit
if [ "$CLEANUP_ONLY" = true ]; then
    exit 0
fi

# Get the absolute path to the plugin directory if installing locally
if [ "$INSTALL_SOURCE" = "local" ]; then
    PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

echo "Installing helm-values-manager plugin..."

# Install plugin based on source
if [ "$INSTALL_SOURCE" = "local" ]; then
    echo "Installing from local directory: $PLUGIN_DIR"
    helm plugin install "$PLUGIN_DIR"
else
    echo "Installing from GitHub: $GITHUB_URL"
    helm plugin install "$GITHUB_URL"
fi

echo -e "\n${GREEN}Running test sequence...${NC}"

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
helm values-manager add-value-config -p "app.config.replicas" -d "Number of replicas" -r $DEBUG_FLAG

# Set values for different environments
echo -e "\n${GREEN}4. Setting values...${NC}"
helm values-manager set-value -p "app.config.name" -v "my-test-app" -d dev $DEBUG_FLAG
helm values-manager set-value -p "app.config.replicas" -v "1" -d dev $DEBUG_FLAG
helm values-manager set-value -p "app.config.name" -v "my-prod-app" -d prod $DEBUG_FLAG

# Verify configurations
echo -e "\n${GREEN}5. Verifying configurations...${NC}"
echo -e "\nhelm-values.json contents:"
cat helm-values.json

echo -e "\n.helm-values.lock contents:"
cat .helm-values.lock

# Generate values files
echo -e "\n${GREEN}6. Generating values files...${NC}"
echo -e "\nGenerating values file for dev deployment..."
helm values-manager generate -d dev $DEBUG_FLAG

# Temporarily disable exit on error for the prod generate command
set +e
echo -e "\nGenerating values file for prod deployment with custom output path..."
mkdir -p output
helm values-manager generate -d prod -o output $DEBUG_FLAG
GENERATE_PROD_STATUS=$?
set -e

# Check if the prod generate command failed
if [ $GENERATE_PROD_STATUS -ne 0 ]; then
    echo -e "\n${RED}Warning: Failed to generate values file for prod deployment.${NC}"
    echo -e "${RED}This is expected because we didn't set a required value for app.config.replicas.${NC}"
fi

# Verify generated files
echo -e "\n${GREEN}7. Verifying generated files...${NC}"
echo -e "\ndev.test-release.values.yaml contents:"
cat dev.test-release.values.yaml

# Only try to display the prod values file if it was successfully generated
if [ -f "output/prod.test-release.values.yaml" ]; then
    echo -e "\noutput/prod.test-release.values.yaml contents:"
    cat output/prod.test-release.values.yaml
else
    echo -e "\n${RED}Note: output/prod.test-release.values.yaml was not generated due to missing required values.${NC}"
fi

echo -e "\n${GREEN}Test sequence completed successfully!${NC}"
