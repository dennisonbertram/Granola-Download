<p align="center">
  <img src="assets/header.png" alt="Granola Download" width="100%" />
</p>

<h1 align="center">Granola Download</h1>

<p align="center">
  Back up your <a href="https://granola.ai">Granola</a> meeting notes and transcripts to your own machine.
</p>

---

## Why?

[Granola](https://granola.ai) is a fantastic AI meeting assistant — it captures transcripts, generates summaries, and organizes your notes beautifully. But your meeting data lives in Granola's cloud, and there's no built-in export.

**Your meetings are yours.** This tool lets you download everything — notes, transcripts, and metadata — so you have a local backup you control. Use it to:

- Keep an offline archive of all your meetings
- Pipe transcripts into your own workflows (Obsidian, search, analysis)
- Have peace of mind that your data is safe regardless of what happens to any service

## Quick Start (macOS)

> Requires the Granola desktop app to be installed and logged in.

**Double-click `download_transcripts.command`** — that's it.

It will automatically authenticate, download all your transcripts, and save them to `transcripts_output/`.

## One-Command Pull (recommended)

Granola's auth tokens are single-use and rotate constantly, so a saved token
goes stale between runs. `pull.py` sidesteps this by always re-extracting a
fresh token from the live Granola app, then downloading and renaming in one go:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Refresh token -> download new transcripts -> rename folders to readable names
python3 pull.py                     # -> ./transcripts_output
python3 pull.py ./my-transcripts    # custom output dir
python3 pull.py -- --overwrite      # pass-through flags to the downloader
```

Folders are named `YYYY-MM-DD_HHMM_Subject_<id8>` (local time), so they sort
chronologically. Re-running only downloads/renames what's new (idempotent).

## Manual Usage

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Download transcripts (auto-extracts tokens from Granola app)
./download_transcripts.command

# Or run directly with your own config
python3 granola/download_transcripts.py ./my-transcripts
```

### Options

```
python3 granola/download_transcripts.py OUTPUT_DIR [options]

  --overwrite          Re-download existing transcripts
  --batch-size N       Documents per batch request (default: 100)
  --page-size N        Documents per page (default: 100)
  --folder-name MODE   Folder naming: id, title, title-id, date-title,
                       date-title-id, date-id (default: id)
  --timeout N          HTTP timeout in seconds (default: 30)
```

### Full Export (Notes + Transcripts)

For a complete export including AI-generated summaries and workspace/folder metadata:

```bash
python3 granola/main.py ./my-export
```

### Browse Your Data

```bash
# List all your workspaces
python3 granola/list_workspaces.py

# List all folders
python3 granola/list_folders.py

# Filter documents by workspace or folder
python3 granola/filter_by_workspace.py ./my-export --list-workspaces
python3 granola/filter_by_folder.py ./my-export --folder-name "Sales"
```

## MCP Server (local stdio)

Expose your transcript archive to MCP clients (e.g. Claude Code) as a local
stdio server. It reads the local archive for search/get/list and can refresh it
on demand. **Credentials are handled internally** — `sync` re-extracts a fresh
token from the Granola app and downloads; no tool ever returns secrets.

Tools: `list_meetings`, `search_transcripts`, `get_transcript`, `sync`,
`archive_stats`.

Runs under [uv](https://docs.astral.sh/uv/) (auto-fetches Python 3.11 + the
`mcp` SDK — no extra venv to manage):

```bash
# Run standalone
./mcp_server/run.sh

# Register with Claude Code (user scope)
claude mcp add granola --scope user -- /absolute/path/to/mcp_server/run.sh
```

The `sync` tool shells out to `pull.py` using the repo's `.venv`, so make sure
the manual install above has been done once.

## Output

```
output/
├── {document_id}/
│   ├── transcript.json        # Raw transcript data
│   ├── transcript.md          # Formatted readable transcript
│   └── transcript_metadata.json
└── transcripts_index.json     # Summary of all downloads
```

The full export (`main.py`) also includes `document.json`, `metadata.json`, and `resume.md` (AI-generated notes) per document.

## Authentication

The tool reads tokens directly from the Granola desktop app's local storage (`~/Library/Application Support/Granola/supabase.json`). No manual configuration needed for most users.

If you prefer manual setup, see the [Setup Guide](docs/SETUP.md).

## Documentation

- [Setup Guide](docs/SETUP.md) — Manual configuration and troubleshooting
- [API Reference](docs/API_REFERENCE.md) — Endpoint documentation
- [Contributing](CONTRIBUTING.md)

## Credits

This work builds on research by [Joseph Thacker](https://josephthacker.com/hacking/2025/05/08/reverse-engineering-granola-notes.html).

## License

[MIT](LICENSE)
