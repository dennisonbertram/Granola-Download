#!/usr/bin/env python3
"""Local stdio MCP server over the Granola transcript archive.

Tools:
  - list_meetings     filter by date range / title keyword
  - search_transcripts full-text search across transcript bodies
  - get_transcript    fetch one meeting's transcript (markdown or raw json)
  - sync              refresh token + download new transcripts + rename

Token handling is INTERNAL: `sync` shells out to the repo's pull.py, which
re-extracts a fresh Granola token from the local app and downloads. No tool
ever returns credentials to the model.

Run via uv (auto-fetches Python 3.11 and the mcp SDK):
    uv run --python 3.11 --with "mcp[cli]" python mcp_server/server.py
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "granola"))

import archive  # noqa: E402  (stdlib-only local module)
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("granola")

# The interpreter that has requests + cryptography (the repo's 3.9 venv).
REPO_PY = REPO / ".venv" / "bin" / "python3"


@mcp.tool()
def list_meetings(since: str = "", until: str = "", query: str = "", limit: int = 50) -> list:
    """List meetings from the local Granola archive, newest first.

    Args:
        since: optional inclusive start date, YYYY-MM-DD.
        until: optional inclusive end date, YYYY-MM-DD.
        query: optional case-insensitive substring to match against the title.
        limit: max rows to return (default 50).

    Returns a list of {document_id, title, date, date_iso, folder}.
    """
    return archive.list_meetings(
        since=since or None, until=until or None, query=query or None, limit=limit
    )


@mcp.tool()
def search_transcripts(query: str, limit: int = 20) -> list:
    """Full-text search across all downloaded transcript bodies.

    Args:
        query: case-insensitive text to find inside transcripts.
        limit: max matching meetings to return (default 20).

    Returns a list of meetings with a snippet around the first hit and a
    match_count per meeting.
    """
    return archive.search_transcripts(query, limit=limit)


@mcp.tool()
def get_transcript(identifier: str, fmt: str = "md") -> dict:
    """Fetch one meeting's full transcript.

    Args:
        identifier: folder name, full or 8-char document_id, or a unique title
            substring.
        fmt: "md" for the formatted transcript (default) or "json" for raw data.

    Returns {document_id, title, date, folder, content} or {error, [matches]}.
    """
    return archive.get_transcript(identifier, fmt=fmt)


@mcp.tool()
def sync() -> dict:
    """Refresh credentials and download any new transcripts into the local
    archive, then rename new folders to readable names.

    Runs the repo's pull.py pipeline (extract fresh token -> download -> rename).
    Returns a summary of the run. Does not expose credentials.
    """
    if not REPO_PY.exists():
        return {"ok": False, "error": f"repo venv python not found at {REPO_PY}"}
    proc = subprocess.run(
        [str(REPO_PY), str(REPO / "pull.py")],
        cwd=str(REPO), capture_output=True, text=True, timeout=900,
    )
    out = proc.stdout
    summary = next((ln.strip() for ln in out.splitlines() if "Done." in ln), "")
    renamed = next((ln.strip() for ln in out.splitlines() if ln.strip().startswith("renamed ")), "")
    result = {
        "ok": proc.returncode == 0,
        "download_summary": summary,
        "renamed": renamed,
        "stats": archive.stats(),
    }
    if proc.returncode != 0:
        # Surface stderr tail for debugging, but never the token (not in stderr).
        result["error"] = (proc.stderr or out)[-800:]
    return result


@mcp.tool()
def archive_stats() -> dict:
    """Return archive location and counts (meetings, earliest/latest date)."""
    return archive.stats()


if __name__ == "__main__":
    mcp.run()  # stdio transport
