#!/bin/bash

# Update the plugin using pip
pip install --target $HELM_PLUGIN_DIR/lib --upgrade .

# Re-run the install script to ensure all files are properly set up
$HELM_PLUGIN_DIR/scripts/install.sh
