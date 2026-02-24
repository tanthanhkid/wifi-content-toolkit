#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== WiFi Marketing Content Toolkit — Install ==="

# Create venv if not exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

source "$SCRIPT_DIR/.venv/bin/activate"

echo "Installing shared..."
pip install -e "$SCRIPT_DIR/shared"

for module in imggen poster tts talkhead vidmake; do
    echo "Installing $module..."
    pip install -e "$SCRIPT_DIR/$module"
done

# Install Playwright Chromium for poster module
echo "Installing Playwright Chromium..."
playwright install chromium || echo "Warning: Playwright chromium install failed. poster module may not work."

echo ""
echo "=== Done! ==="
echo "Activate venv: source $SCRIPT_DIR/.venv/bin/activate"
echo "Run setup:     wfm-setup"
