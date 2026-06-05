#!/usr/bin/env bash
# Launch the Granola MCP stdio server under uv (auto-fetches Python 3.11 + mcp).
# Registered with Claude Code; uses absolute uv path so it works regardless of
# the launching process's PATH.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /Users/dennison/.local/bin/uv run --python 3.11 --with "mcp[cli]" \
    python "$DIR/server.py"
