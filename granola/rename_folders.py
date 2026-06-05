#!/usr/bin/env python3
"""Rename transcript folders from raw document IDs to readable names.

Target name format:  YYYY-MM-DD_HHMM_Subject_<id8>

- Date/time come from each meeting's ``meeting_date`` (falling back to
  ``created_at``), converted to the machine's LOCAL timezone so they match
  wall-clock time.
- Subject is the meeting title, sanitized for the filesystem.
- The 8-char document-ID suffix keeps names unique and traceable.

Idempotent: a folder is only renamed when its current name still equals the
raw ``document_id`` from its metadata, so re-running after an incremental
download only touches freshly-downloaded folders.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def _parse(ts):
    if not ts:
        return None
    try:
        # Stored as UTC ISO (e.g. 2025-03-27T17:30:13.048Z). Convert to local.
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def _sanitize(title):
    t = (title or "Untitled").strip()
    t = re.sub(r"[<>]", "-", t)          # angle brackets -> dash
    t = re.sub(r"[/\\:]", "-", t)        # path separators / drive colon
    t = re.sub(r"[\x00-\x1f]", "", t)    # strip control chars
    t = re.sub(r"\s+", " ", t).strip()
    return t[:80].rstrip(" .-") or "Untitled"


def build_name(meta):
    """Build the target folder name from a transcript_metadata.json dict."""
    dt = _parse(meta.get("meeting_date")) or _parse(meta.get("created_at"))
    stamp = dt.strftime("%Y-%m-%d_%H%M") if dt else "0000-00-00_0000"
    return f"{stamp}_{_sanitize(meta.get('title'))}_{meta.get('document_id', '')[:8]}"


def rename_all(output_dir):
    """Rename every still-ID-named folder under ``output_dir``.

    Returns a list of the new folder names that were created this run.
    """
    root = Path(output_dir)
    renamed = []
    if not root.is_dir():
        return renamed
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / "transcript_metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Only rename folders still named by their raw document_id.
        if d.name != meta.get("document_id", ""):
            continue
        new_name = build_name(meta)
        target = root / new_name
        if target.exists():
            continue
        d.rename(target)
        renamed.append(new_name)
    return renamed


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "transcripts_output"
    renamed = rename_all(output_dir)
    print(f"renamed {len(renamed)} folder(s)")
    for n in renamed:
        print(" ", n)


if __name__ == "__main__":
    main()
