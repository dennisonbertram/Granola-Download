<p align="center">
  <img src="assets/header.png" alt="Granola Download" width="100%" />
</p>

<h1 align="center">Granola Download</h1>

<p align="center">
  Back up and search your <a href="https://granola.ai">Granola</a> meeting transcripts — from your AI agent or the command line.
</p>

---

## Why?

[Granola](https://granola.ai) captures great transcripts and notes, but your data
lives in its cloud and there's no built-in export. **Your meetings are yours.**
This tool downloads everything to your own machine so you can archive it, search
it, and pipe it into your own workflows.

> **macOS only.** Requires the **Granola desktop app installed and logged in** —
> the auth token is read (decrypted) straight from the app's local storage, so
> there's nothing to configure.

---

## Install

### ⭐ Recommended: as an AI skill (`npx skills`)

Install the `granola` skill into your AI agent (Claude Code, Codex, Cursor, …):

```bash
npx skills add dennisonbertram/Granola-Download
```

Then just ask your agent — or use the slash command:

```
/granola                       # back up the latest transcripts
/granola search "pricing"      # full-text search across all meetings
/granola get "Weekly Sync"     # print one transcript (by title, date, or id)
/granola stats                 # how many meetings, date range
```

The skill bootstraps everything on first run (clones this repo to a stable
location and sets up its environment), refreshes your Granola token, and saves
transcripts locally. Nothing else to set up.

### Alternative: standalone (no AI agent)

```bash
git clone https://github.com/dennisonbertram/Granola-Download
cd Granola-Download
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python3 pull.py                 # back up to ./transcripts_output
```

…or on macOS, **double-click `download_transcripts.command`** — it sets up the
environment and runs the same backup.

---

## The `pull` command

`pull.py` is the one command that does everything, every time:

1. **Refreshes your token.** Granola's tokens are single-use and rotate
   constantly, so a saved one goes stale between runs. `pull.py` always
   re-extracts a fresh token from the live app first — so it just works.
2. **Downloads only what's new** (skips already-downloaded meetings).
3. **Renames folders** to `YYYY-MM-DD_HHMM_Subject_<id8>` (local time) so they
   sort chronologically. Idempotent — safe to run repeatedly.

```bash
python3 pull.py                 # -> ./transcripts_output
python3 pull.py ./my-archive    # custom output dir
python3 pull.py -- --overwrite  # pass flags through to the downloader
```

---

## MCP server (search your transcripts from any MCP client)

A local stdio MCP server exposes your archive to clients like Claude Code, the
Claude desktop app, and Codex.

**Tools:** `search_transcripts`, `list_meetings`, `get_transcript`, `sync`,
`archive_stats`. Credentials are handled **internally** — `sync` refreshes the
token and downloads; no tool ever returns secrets.

Runs under [uv](https://docs.astral.sh/uv/) (auto-fetches Python 3.11 + the `mcp`
SDK — no extra setup):

```bash
# Claude Code
claude mcp add granola --scope user -- "$(pwd)/mcp_server/run.sh"
```

<details>
<summary>Claude desktop app · Codex</summary>

**Claude desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{ "mcpServers": { "granola": { "command": "/ABSOLUTE/PATH/Granola-Download/mcp_server/run.sh" } } }
```

**Codex** — add to `~/.codex/config.toml`:

```toml
[mcp_servers.granola]
command = "/ABSOLUTE/PATH/Granola-Download/mcp_server/run.sh"
args = []
```

Restart the app afterward.
</details>

---

## Output

```
transcripts_output/
├── 2026-06-04_1538_Eigen Layer strategy_ccbb2f18/
│   ├── transcript.md            # formatted, readable transcript
│   ├── transcript.json          # raw transcript data
│   └── transcript_metadata.json
└── transcripts_index.json       # summary of the run
```

### Full export (notes + AI summaries)

For a complete export including AI-generated notes and workspace/folder metadata:

```bash
python3 granola/main.py ./my-export   # adds document.json, metadata.json, resume.md per meeting
```

### Browse / filter

```bash
python3 granola/list_workspaces.py
python3 granola/list_folders.py
python3 granola/filter_by_folder.py ./my-export --folder-name "Sales"
```

### Downloader options

```
python3 granola/download_transcripts.py OUTPUT_DIR [options]
  --overwrite          Re-download existing transcripts
  --batch-size N       Documents per batch request (default: 100)
  --page-size N        Documents per page (default: 100)
  --folder-name MODE   id | title | title-id | date-title | date-title-id | date-id
  --timeout N          HTTP timeout in seconds (default: 30)
```

---

## How it works / troubleshooting

- **Auth:** tokens are decrypted from the Granola app's local storage
  (`storage.dek` + `supabase.json.enc`) via your macOS keychain. See
  [`extract_config.py`](extract_config.py) and the [Setup Guide](docs/SETUP.md).
- **"Failed to obtain access token" / HTTP 400:** the saved token went stale.
  Just re-run `pull.py` — it re-extracts a fresh one. If extraction itself
  fails, make sure the Granola app is installed and logged in.
- **Your data stays private:** `config.json`, `transcripts_output/`, and
  `.venv/` are gitignored and never committed.

## Documentation

- [Setup Guide](docs/SETUP.md) — manual configuration and troubleshooting
- [API Reference](docs/API_REFERENCE.md) — endpoint documentation
- [Contributing](CONTRIBUTING.md)

## Credits

Builds on research by [Joseph Thacker](https://josephthacker.com/hacking/2025/05/08/reverse-engineering-granola-notes.html).

## License

[MIT](LICENSE)
