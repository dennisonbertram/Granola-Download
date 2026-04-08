# Setup Guide

## Prerequisites

- Python 3.8+
- The [Granola](https://granola.ai) desktop app installed and logged in on your Mac

## Quick Start (macOS)

The easiest way to get started is to double-click `download_transcripts.command`. It handles everything automatically:

1. Creates a Python virtual environment
2. Installs dependencies
3. Extracts your authentication tokens from the Granola app
4. Downloads all your transcripts

## Manual Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure authentication

**Option A: Automatic (recommended)**

If you have the Granola desktop app logged in, just run `download_transcripts.command` and it will create `config.json` for you automatically.

**Option B: Manual**

1. Copy the template:
   ```bash
   cp config.json.template config.json
   ```

2. Open Granola's local token storage:
   ```bash
   cat ~/Library/Application\ Support/Granola/supabase.json
   ```

3. Extract the `refresh_token`:
   ```bash
   cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .refresh_token'
   ```

4. Extract the `client_id` from the JWT:
   ```bash
   cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .access_token' | cut -d. -f2 | base64 -d 2>/dev/null | jq -r '.iss' | grep -o 'client_[^"]*'
   ```

5. Add both values to `config.json`

### 3. Run

```bash
python3 download_transcripts.py ./my-transcripts
```

## Token Lifecycle

Granola uses OAuth 2.0 with refresh token rotation (via WorkOS):

- **Access tokens** expire after 1 hour
- **Refresh tokens** are single-use — each use returns a new one
- The tool automatically rotates tokens and saves them back to `config.json`
- If your refresh token expires (e.g., from not running the tool for a while), just delete `config.json` and re-run — it will extract fresh tokens from the Granola app

## Keeping Tokens Alive

If you want continuous access without re-extracting tokens, run the tool periodically:

```bash
# Via cron (every 5 minutes)
*/5 * * * * cd /path/to/repo && python3 main.py /path/to/output
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Config file not found" | Run `download_transcripts.command` or create `config.json` manually |
| "Failed to refresh access token" | Delete `config.json` and re-run — your token expired |
| "Unsupported client" | Make sure you're using a recent `client_id` from the Granola app |
| Token keeps expiring | Quit Granola (`Cmd+Q`) after extracting tokens so it doesn't invalidate them |
