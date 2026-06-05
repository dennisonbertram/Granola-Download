---
name: granola
description: "Back up and query Granola meeting transcripts. Refreshes Granola's auto-rotating auth token, downloads new transcripts locally, names them readably, and searches/reads the archive. Use when asked to 'pull granola', 'download my transcripts', 'sync granola', 'back up my meetings', 'search my transcripts', 'find that meeting', or to refresh Granola credentials."
version: 1.0.0
user_invocable: true
---

# Granola

Back up your [Granola](https://granola.ai) meeting transcripts to local disk and
query them. Granola encrypts its local storage and uses single-use WorkOS auth
tokens that rotate on every refresh, so the key trick is: **always re-extract a
fresh token from the live app immediately before downloading.** The `pull.py`
pipeline does this for you.

Repo lives at `~/develop/Granola-Download`. Run all commands from there.

## Usage

```
/granola              # pull latest (refresh token → download new → rename)
/granola search XYZ   # full-text search across transcript bodies
/granola get <id|title|date>   # print one transcript
/granola stats        # archive location + counts
```

## Trigger phrases

"pull granola", "sync granola", "download my transcripts", "back up my meetings",
"search my transcripts", "find that meeting about …", "refresh granola token".

---

## Step 1 — Pull (default action)

One command does everything; it re-extracts a fresh token first, so it "just works":

```bash
cd ~/develop/Granola-Download && source .venv/bin/activate && python3 pull.py
```

- Downloads only **new** documents (skips already-downloaded by `document_id`).
- Renames new folders to `YYYY-MM-DD_HHMM_Subject_<id8>` (local time, sorts
  chronologically). Idempotent.
- Output lands in `transcripts_output/`.

If the first install hasn't happened yet:

```bash
cd ~/develop/Granola-Download
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### Why pulls fail with a 400 / "Failed to obtain access token"

The saved `config.json` token went stale (WorkOS rotated it, single-use).
`pull.py` already re-extracts before downloading, so just re-run it. Only if
extraction itself fails: ensure the **Granola desktop app is installed and
logged in** (the token is decrypted from its local keychain + `storage.dek`).

## Step 2 — Search / read the archive

Prefer the **`granola` MCP server tools** if available in this session
(`mcp__granola__search_transcripts`, `__list_meetings`, `__get_transcript`,
`__sync`, `__archive_stats`). Otherwise use the stdlib reader directly:

```bash
cd ~/develop/Granola-Download && python3 - <<'PY'
import sys; sys.path.insert(0, "granola")
import archive
# search bodies:
for r in archive.search_transcripts("<query>", limit=10):
    print(r["date"], "|", r["title"], "| hits", r["match_count"])
    print("   ", r["snippet"])
# list by date/title:
# archive.list_meetings(since="2026-01-01", query="weekly", limit=20)
# read one (folder name, full or 8-char id, or unique title substring):
# print(archive.get_transcript("<id-or-title>")["content"])
PY
```

## Step 3 — Credentials (handle internally, do NOT print)

The user may want a working session, not the raw secret. Refreshing the token IS
running `pull.py` (or `python3 extract_config.py` alone, which rewrites
`config.json`). **Never echo `config.json`, the access token, or refresh token
into the conversation** — they're live credentials. If the user explicitly asks
to see them, confirm first and point them at the gitignored `config.json`.

---

## Reference

| File | Purpose |
|------|---------|
| `pull.py` | One-command pipeline: extract token → download → rename |
| `extract_config.py` | Decrypt Granola storage → fresh `config.json` (token + client_id) |
| `granola/download_transcripts.py` | Transcript-only download (`main.py` = full export incl. AI notes) |
| `granola/rename_folders.py` | Idempotent readable-name renamer |
| `granola/archive.py` | Stdlib reader: `list_meetings` / `search_transcripts` / `get_transcript` / `stats` |
| `mcp_server/server.py` | Local stdio MCP server exposing the above |

## Guardrails

- `config.json`, `transcripts_output/`, and `.venv/` are **gitignored** — never
  commit them or paste their contents.
- The token rotates constantly; don't cache it anywhere. Re-run `pull.py`.
- Full export (AI summaries + workspace/folder metadata):
  `python3 granola/main.py ./my-export`.
