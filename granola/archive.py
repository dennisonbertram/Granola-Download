#!/usr/bin/env python3
"""Read-only access to the local Granola transcript archive.

Stdlib-only so it imports cleanly under any Python (including the MCP server's
separate interpreter). Operates over a ``transcripts_output`` directory whose
folders each contain transcript.md / transcript.json / transcript_metadata.json.
"""
import json
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "transcripts_output"


def _archive_root(output_dir=None):
    return Path(output_dir) if output_dir else DEFAULT_OUTPUT


def _meeting_dt(meta):
    for key in ("meeting_date", "created_at"):
        ts = meta.get(key)
        if not ts:
            continue
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        except Exception:
            continue
    return None


def _iter_folders(root):
    if not root.is_dir():
        return
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / "transcript_metadata.json").exists():
            yield d


def _load_meta(folder):
    try:
        return json.loads((folder / "transcript_metadata.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def _summary(folder, meta):
    dt = _meeting_dt(meta)
    return {
        "document_id": meta.get("document_id"),
        "title": meta.get("title") or "Untitled",
        "date": dt.strftime("%Y-%m-%d %H:%M") if dt else None,
        "date_iso": dt.isoformat() if dt else None,
        "folder": folder.name,
    }


def _within(dt, since, until):
    if dt is None:
        return since is None and until is None
    d = dt.strftime("%Y-%m-%d")
    if since and d < since:
        return False
    if until and d > until:
        return False
    return True


def list_meetings(output_dir=None, since=None, until=None, query=None, limit=50):
    """List meetings, optionally filtered by date range (YYYY-MM-DD) and/or a
    case-insensitive substring ``query`` against the title. Newest first."""
    root = _archive_root(output_dir)
    q = (query or "").lower().strip()
    rows = []
    for folder in _iter_folders(root):
        meta = _load_meta(folder)
        if not meta:
            continue
        if q and q not in (meta.get("title") or "").lower():
            continue
        if not _within(_meeting_dt(meta), since, until):
            continue
        rows.append(_summary(folder, meta))
    rows.sort(key=lambda r: r["date_iso"] or "", reverse=True)
    return rows[: max(0, limit)] if limit else rows


def search_transcripts(query, output_dir=None, limit=20, context=160):
    """Full-text search across transcript bodies. Returns matches with a snippet
    around the first hit. Case-insensitive substring match."""
    root = _archive_root(output_dir)
    q = (query or "").lower().strip()
    if not q:
        return []
    results = []
    for folder in _iter_folders(root):
        md = folder / "transcript.md"
        if not md.exists():
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        idx = text.lower().find(q)
        if idx == -1:
            continue
        meta = _load_meta(folder) or {}
        start = max(0, idx - context // 2)
        end = min(len(text), idx + len(q) + context // 2)
        snippet = text[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "…" + snippet
        if end < len(text):
            snippet = snippet + "…"
        hit = _summary(folder, meta)
        hit["snippet"] = snippet
        hit["match_count"] = text.lower().count(q)
        results.append(hit)
        if len(results) >= limit:
            break
    return results


def get_transcript(identifier, output_dir=None, fmt="md"):
    """Resolve a meeting by exact folder name, full or 8-char document_id, or a
    case-insensitive title substring, and return its transcript.

    ``fmt`` = "md" (formatted) or "json" (raw transcript data). Returns a dict
    with the metadata summary plus ``content``, or ``{"error": ...}``.
    """
    root = _archive_root(output_dir)
    ident = (identifier or "").strip()
    if not ident:
        return {"error": "empty identifier"}

    exact = root / ident
    candidates = []
    if exact.is_dir() and (exact / "transcript_metadata.json").exists():
        candidates = [exact]
    else:
        il = ident.lower()
        for folder in _iter_folders(root):
            meta = _load_meta(folder) or {}
            doc_id = (meta.get("document_id") or "")
            if doc_id == ident or doc_id[:8] == ident or il in folder.name.lower() \
                    or il in (meta.get("title") or "").lower():
                candidates.append(folder)

    if not candidates:
        return {"error": f"no meeting matched {identifier!r}"}
    if len(candidates) > 1:
        return {
            "error": f"{len(candidates)} meetings matched {identifier!r}; be more specific",
            "matches": [c.name for c in candidates[:10]],
        }

    folder = candidates[0]
    meta = _load_meta(folder) or {}
    fname = "transcript.json" if fmt == "json" else "transcript.md"
    fpath = folder / fname
    if not fpath.exists():
        return {"error": f"{fname} missing in {folder.name}"}
    out = _summary(folder, meta)
    out["content"] = fpath.read_text(encoding="utf-8")
    return out


def stats(output_dir=None):
    root = _archive_root(output_dir)
    folders = list(_iter_folders(root))
    dates = [r["date_iso"] for r in (_summary(f, _load_meta(f) or {}) for f in folders) if r["date_iso"]]
    return {
        "archive_dir": str(root),
        "meetings": len(folders),
        "earliest": min(dates)[:10] if dates else None,
        "latest": max(dates)[:10] if dates else None,
    }
