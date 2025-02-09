#!/bin/bash

# Check if Python 3.8 or higher is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
  # Python version is >= 3.8, proceed with installation
  python3 -m pip install -e .
else
  echo "Error: Python 3.8 or higher is required (found $python_version)"
  exit 1
fi

mkdir -p $HELM_PLUGIN_DIR/bin

# Create Python script with error handling
cat > $HELM_PLUGIN_DIR/bin/helm_values_manager.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

try:
    sys.path.insert(0, os.path.join(os.environ["HELM_PLUGIN_DIR"], "lib"))
    from helm_values_manager import helm_values_manager
except ImportError as e:
    print(f"Error: Failed to import helm_values_manager: {e}", file=sys.stderr)
    print("This might be due to missing dependencies or incorrect installation.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    sys.exit(helm_values_manager())
EOF

# Create wrapper script with error handling
cat > $HELM_PLUGIN_DIR/bin/wrapper.sh << 'EOF'
#!/bin/sh

# Ensure HELM_PLUGIN_DIR is set
if [ -z "$HELM_PLUGIN_DIR" ]; then
    echo "Error: HELM_PLUGIN_DIR environment variable is not set"
    exit 1
fi

# Ensure the Python script exists
if [ ! -f "$HELM_PLUGIN_DIR/bin/helm_values_manager.py" ]; then
    echo "Error: helm_values_manager.py not found"
    exit 1
fi

# Run the Python script with proper error handling
python3 "$HELM_PLUGIN_DIR/bin/helm_values_manager.py" "$@"
EOF

# Create Windows wrapper script
cat > $HELM_PLUGIN_DIR/bin/wrapper.bat << 'EOF'
@echo off
setlocal

if "%HELM_PLUGIN_DIR%"=="" (
    echo Error: HELM_PLUGIN_DIR environment variable is not set
    exit /b 1
)

if not exist "%HELM_PLUGIN_DIR%\bin\helm_values_manager.py" (
    echo Error: helm_values_manager.py not found
    exit /b 1
)

python "%HELM_PLUGIN_DIR%\bin\helm_values_manager.py" %*
EOF

chmod +x $HELM_PLUGIN_DIR/bin/helm_values_manager.py
chmod +x $HELM_PLUGIN_DIR/bin/wrapper.sh

echo "helm-values-manager plugin installed successfully"
