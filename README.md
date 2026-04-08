<p align="center">
  <img src="assets/header.svg" alt="Granola Download" width="100%" />
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

## Manual Usage

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Download transcripts (auto-extracts tokens from Granola app)
./download_transcripts.command

# Or run directly with your own config
python3 download_transcripts.py ./my-transcripts
```

### Options

```
python3 download_transcripts.py OUTPUT_DIR [options]

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
python3 main.py ./my-export
```

### Browse Your Data

```bash
# List all your workspaces
python3 list_workspaces.py

# List all folders
python3 list_folders.py

# Filter documents by workspace or folder
python3 filter_by_workspace.py ./my-export --list-workspaces
python3 filter_by_folder.py ./my-export --folder-name "Sales"
```

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
