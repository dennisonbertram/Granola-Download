#!/bin/bash
# Double-click entry point: set up the venv, then run the full pull pipeline
# (refresh token -> download new transcripts -> rename to readable folders).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"
VENV_PY="$SCRIPT_DIR/$VENV_DIR/bin/python"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/transcripts_output}"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
"$VENV_PY" -m pip install -q -r requirements.txt

# pull.py always re-extracts a fresh token from the live Granola app first,
# so this works even though Granola's saved token rotates constantly.
if ! "$VENV_PY" pull.py "$OUTPUT_DIR"; then
  echo ""
  echo "Pull failed. Make sure the Granola desktop app is installed and logged in,"
  echo "then run this again."
  read -n 1 -s -r -p "Press any key to close..."
  exit 1
fi

echo ""
echo "Done. Output: $OUTPUT_DIR"
read -n 1 -s -r -p "Press any key to close..."
