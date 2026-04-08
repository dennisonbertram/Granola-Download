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

   The file looks like:
   ```json
   {
     "workos_tokens": "{\"access_token\":\"<JWT>\",\"expires_in\":21599,\"refresh_token\":\"<TOKEN>\",\"token_type\":\"Bearer\",\"obtained_at\":1763065919448,\"session_id\":\"<ID>\",\"external_id\":\"<ID>\"}",
     "session_id": "<REDACTED>",
     "user_info": "{...}"
   }
   ```
   Note: `workos_tokens` is a JSON-encoded string, not a nested object.

3. Extract the `refresh_token`:
   ```bash
   cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .refresh_token'
   ```

4. Extract the `client_id` from the JWT:
   ```bash
   cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .access_token' | cut -d. -f2 | base64 -d 2>/dev/null | jq -r '.iss' | grep -o 'client_[^"]*'
   ```
   The `client_id` is the `client_<...>` suffix of the `iss` field in the JWT payload, e.g. `client_01abc...`.

5. Add both values to `config.json`

6. **Preserve your session** — quit Granola completely (`Cmd+Q`) after extracting tokens. If you want to prevent Granola from invalidating the refresh token the next time it launches, remove its app data:
   ```bash
   rm -rf ~/Library/Application\ Support/Granola/
   ```
   This stops the app from rotating the token on its own startup sequence.

### 3. Run

```bash
python3 granola/download_transcripts.py ./my-transcripts
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
*/5 * * * * cd /path/to/repo && python3 granola/main.py /path/to/output
```

## Alternative Token Extraction

If you don't have `jq` installed, you can decode the tokens manually:

1. Copy the value of `workos_tokens` from `supabase.json` (it's an escaped JSON string)
2. Parse it as JSON and copy `refresh_token` and `access_token`
3. Base64-decode the middle section (payload) of the `access_token` JWT
4. The `iss` field contains the `client_id` — e.g. `https://auth.granola.ai/user_management/client_01abc...`

### Browser Developer Tools

For web-based flows, open `https://app.granola.ai` in Chrome:
- Open DevTools (`Cmd+Option+I`) → Network tab
- Filter for `authenticate` or `workos`
- Look for the authentication response containing the tokens

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Config file not found" | Run `download_transcripts.command` or create `config.json` manually |
| "Failed to refresh access token" | Delete `config.json` and re-run — your token expired |
| "Unsupported client" | Make sure you're using a recent `client_id` from the Granola app |
| "Token already exchanged" | The refresh token was already used — re-extract fresh tokens from the Granola app |
| "Invalid grant" | Token expired or revoked — re-authenticate and follow step 6 to preserve the session |
| "Missing client_id" | Verify `config.json` contains both `refresh_token` and `client_id` |
| Token keeps expiring | Quit Granola (`Cmd+Q`) and/or remove `~/Library/Application Support/Granola/` after extracting |
