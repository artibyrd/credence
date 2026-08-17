#!/usr/bin/env sh
# Credence Canonical One-Line Installer
# curl -fsSL https://credence.run/install | sh
set -e

echo "=== Installing Credence CLI ==="

# Check Python 3.12+
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required. Please install Python 3.12+ (https://python.org)." >&2
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]; }; then
  echo "Error: Python 3.12+ is required. Found: Python $PY_VERSION" >&2
  exit 1
fi

# Prefer pipx if available, fallback to pip --user
if command -v pipx >/dev/null 2>&1; then
  echo "Installing via pipx..."
  pipx install credence || pipx upgrade credence
elif python3 -m pip --version >/dev/null 2>&1; then
  echo "Installing via pip --user..."
  python3 -m pip install --user --upgrade credence
else
  echo "Error: Neither pipx nor pip found. Please install pip or pipx." >&2
  exit 1
fi

echo ""
echo "=== Credence successfully installed! ==="
echo "Run 'credence --help' or 'credence identity show' to get started."
