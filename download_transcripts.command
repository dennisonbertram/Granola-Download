#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"
VENV_PY="$SCRIPT_DIR/$VENV_DIR/bin/python"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/transcripts_output}"
FOLDER_NAME="${FOLDER_NAME:-date-title-id}"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_PY" -m pip install -r requirements.txt >/dev/null

if [ ! -f "config.json" ]; then
  SUPABASE_PATH="$HOME/Library/Application Support/Granola/supabase.json"
  if [ ! -f "$SUPABASE_PATH" ]; then
    echo "Missing config.json and Granola supabase.json."
    echo "Open Granola, log in, then re-run this tool."
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
  fi

  "$VENV_PY" - <<'PY'
import base64
import json
from pathlib import Path
import sys

supabase_path = Path.home() / 'Library' / 'Application Support' / 'Granola' / 'supabase.json'

try:
    data = json.loads(supabase_path.read_text())
except Exception as exc:
    print(f"Failed to read {supabase_path}: {exc}")
    sys.exit(1)

workos_raw = data.get('workos_tokens')
if not workos_raw:
    print("workos_tokens missing in supabase.json")
    sys.exit(1)

try:
    workos = json.loads(workos_raw)
except Exception as exc:
    print(f"Failed to parse workos_tokens JSON: {exc}")
    sys.exit(1)

refresh_token = workos.get('refresh_token')
access_token = workos.get('access_token')
if not refresh_token or not access_token:
    print("refresh_token or access_token missing in workos_tokens")
    sys.exit(1)

parts = access_token.split('.')
if len(parts) < 2:
    print("access_token does not look like a JWT")
    sys.exit(1)

payload = parts[1]
pad = '=' * (-len(payload) % 4)
try:
    decoded = base64.urlsafe_b64decode(payload + pad)
    payload_json = json.loads(decoded)
except Exception as exc:
    print(f"Failed to decode access_token payload: {exc}")
    sys.exit(1)

iss = payload_json.get('iss', '')
client_id = None
if 'client_' in iss:
    client_id = 'client_' + iss.split('client_')[-1]

if not client_id:
    print("client_id not found in access_token issuer")
    sys.exit(1)

config = {
    "refresh_token": refresh_token,
    "client_id": client_id,
}

Path('config.json').write_text(json.dumps(config, indent=2))
print("config.json created")
PY
fi

"$VENV_PY" download_transcripts.py "$OUTPUT_DIR" --folder-name "$FOLDER_NAME"

echo ""
echo "Done. Output: $OUTPUT_DIR"
read -n 1 -s -r -p "Press any key to close..."
