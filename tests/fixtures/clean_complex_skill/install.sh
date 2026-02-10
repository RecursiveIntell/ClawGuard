#!/bin/bash
# Install dependencies for data-pipeline skill

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Setting up data-pipeline skill..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Install dependencies
"$VENV_DIR/bin/pip" install --quiet pandas jsonschema

echo "Data pipeline dependencies installed successfully."
