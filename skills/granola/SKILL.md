---
name: granola
description: "Back up and query Granola meeting transcripts. Refreshes Granola's auto-rotating auth token, downloads new transcripts locally, names them readably, and searches/reads the archive. Use when asked to 'pull granola', 'download my transcripts', 'sync granola', 'back up my meetings', 'search my transcripts', 'find that meeting', or to refresh Granola credentials."
version: 1.1.0
user_invocable: true
---

# Granola

Back up your [Granola](https://granola.ai) meeting transcripts to local disk and
query them. Granola encrypts its local storage and uses single-use auth tokens
that rotate on every refresh, so the key trick is: **always re-extract a fresh
token from the live app immediately before downloading.** The bundled `pull.py`
pipeline does this for you.

> Requires the **Granola desktop app installed and logged in** (the token is
> decrypted from its local keychain entry). macOS only.

## Usage

```
/granola              # pull latest (refresh token → download new → rename)
/granola search XYZ   # full-text search across transcript bodies
/granola get <id|title|date>   # print one transcript
/granola stats        # archive location + counts
```

Trigger phrases: "pull granola", "sync granola", "download my transcripts",
"back up my meetings", "search my transcripts", "find that meeting about …",
"refresh granola token".

---

## Step 0 — Locate or install the toolkit (do this first, every run)

The skill needs the Granola-Download repo (scripts + venv). Find an existing
checkout or install one to a stable location. Run this bootstrap; `$GRANOLA`
is the repo path for all later steps:

```bash
set -e
GRANOLA=""
for d in "$HOME/develop/Granola-Download" "$HOME/Granola-Download" \
         "$HOME/.local/share/granola-download"; do
  [ -f "$d/pull.py" ] && GRANOLA="$d" && break
done
if [ -z "$GRANOLA" ]; then
  GRANOLA="$HOME/.local/share/granola-download"
  git clone https://github.com/dennisonbertram/Granola-Download "$GRANOLA"
fi
# Ensure the venv + deps exist (idempotent).
if [ ! -x "$GRANOLA/.venv/bin/python" ]; then
  python3 -m venv "$GRANOLA/.venv"
fi
"$GRANOLA/.venv/bin/python" -m pip install -q -r "$GRANOLA/requirements.txt"
echo "GRANOLA=$GRANOLA"
```

Use `$GRANOLA/.venv/bin/python` as the interpreter for every command below.

## Step 1 — Pull (default action)

```bash
"$GRANOLA/.venv/bin/python" "$GRANOLA/pull.py"
```

- Re-extracts a fresh token, then downloads only **new** documents (skips
  already-downloaded by `document_id`).
- Renames new folders to `YYYY-MM-DD_HHMM_Subject_<id8>` (local time, sorts
  chronologically). Idempotent.
- Output lands in `$GRANOLA/transcripts_output/`.

**If a pull fails with a 400 / "Failed to obtain access token":** the saved
token went stale (it rotates, single-use). `pull.py` already re-extracts before
downloading, so just run it again. If extraction itself fails, confirm the
Granola desktop app is installed and logged in.

## Step 2 — Search / read the archive

Prefer the **`granola` MCP server tools** if present in this session
(`mcp__granola__search_transcripts`, `__list_meetings`, `__get_transcript`,
`__sync`, `__archive_stats`). Otherwise use the bundled stdlib reader:

```bash
"$GRANOLA/.venv/bin/python" - "$GRANOLA" <<'PY'
import sys; root = sys.argv[1]; sys.path.insert(0, f"{root}/granola")
import archive
out = f"{root}/transcripts_output"
# search bodies:
for r in archive.search_transcripts("QUERY", output_dir=out, limit=10):
    print(r["date"], "|", r["title"], "| hits", r["match_count"], "\n   ", r["snippet"])
# list by date/title:  archive.list_meetings(output_dir=out, since="2026-01-01", query="weekly")
# read one:            print(archive.get_transcript("ID-OR-TITLE", output_dir=out)["content"])
PY
```

## Step 3 — Credentials (handle internally, never print)

Refreshing the token just means running `pull.py` (or `extract_config.py`, which
rewrites `config.json`). **Never echo `config.json`, the access token, or the
refresh token into the conversation** — they are live credentials. If the user
explicitly wants to see them, confirm first and point them at the gitignored
`config.json`.

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
- The token rotates constantly; don't cache it. Re-run `pull.py`.
- Full export (AI summaries + workspace/folder metadata):
  `"$GRANOLA/.venv/bin/python" "$GRANOLA/granola/main.py" ./my-export`.
