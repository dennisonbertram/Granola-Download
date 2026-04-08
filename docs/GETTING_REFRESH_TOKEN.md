# Obtaining Granola Refresh Token and Client ID

Guide for extracting refresh tokens and `client_id` from Granola on macOS for API reverse engineering.

## Quick Start (Recommended Method)

### Step 1: Login to Granola

Launch the Granola app and log in to create a valid session.

### Step 2: Extract Refresh Token and Client ID

The refresh token and `client_id` are stored in `supabase.json` in Granola's application data directory.

**View the file:**

```bash
cat ~/Library/Application\ Support/Granola/supabase.json
```

**File structure:**

```json
{
  "workos_tokens": "{\"access_token\":\"<REDACTED>\",\"expires_in\":21599,\"refresh_token\":\"<REDACTED>\",\"token_type\":\"Bearer\",\"obtained_at\":1763065919448,\"session_id\":\"<REDACTED>\",\"external_id\":\"<REDACTED>\"}",
  "session_id": "<REDACTED>",
  "user_info": "{...}"
}
```

**Note:** The `workos_tokens` field contains a JSON string (escaped), not a JSON object.

**Extract refresh_token using jq:**

```bash
cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .refresh_token'
```

**Extract client_id from the JWT access token:**

```bash
cat ~/Library/Application\ Support/Granola/supabase.json | jq -r '.workos_tokens | fromjson | .access_token' | cut -d. -f2 | base64 -d 2>/dev/null | jq -r '.iss' | grep -o 'client_[^"]*'
```

**Or extract manually:**

1. Copy the value of the `workos_tokens` field (it's a JSON string)
2. Parse it as JSON to extract:
   - `refresh_token` - looks like: `22oWVolI9TRlthI2J5asHbfyx`
   - `access_token` - a JWT token
3. Decode the JWT `access_token` (base64 decode the middle section)
4. Look at the `iss` (issuer) field - it contains the `client_id` at the end

Example `iss` field:
```
https://auth.granola.ai/user_management/client_<REDACTED>
```

The `client_id` is: `client_<REDACTED>`

### Step 3: Preserve Your Session

**IMPORTANT:** To prevent the refresh token from expiring when Granola starts next time:

1. **Login to your Granola app** (to generate a valid session)
2. **Extract the refresh token and client_id** from `supabase.json` (as shown above)
3. **Quit Granola completely** (Cmd+Q)
4. **Remove Application Support data** to prevent session conflicts:
   ```bash
   rm -rf ~/Library/Application\ Support/Granola/
   ```

**Why this works:** Once you remove the Granola app data, the app can't invalidate your extracted refresh token when it starts up again. Your script will keep the token alive through continuous rotation.

### Step 4: Configure Your Script

Create `config.json`:

```json
{
  "refresh_token": "your-refresh-token-from-supabase.json",
  "client_id": "client_<REDACTED>"
}
```

### Step 5: Keep Session Alive

**CRITICAL:** Refresh the token every ~5 minutes to keep the session alive.

**Why ~5 minutes?** While access tokens last 1 hour, refreshing frequently ensures:
- The refresh token doesn't expire from inactivity
- You always have a fresh, valid token
- Your session stays active even if Granola's backend has shorter session timeouts

**Run your sync script regularly:**

```bash
# Run once
python3 main.py /path/to/output

# Or schedule with cron (every 5 minutes)
*/5 * * * * cd /path/to/repo && python3 main.py /path/to/output
```

The `token_manager.py` automatically:
- Rotates the refresh token on each use
- Saves the new refresh token back to `config.json`
- Keeps your session alive indefinitely

---

## Token Lifecycle

**CRITICAL: Refresh tokens CANNOT be reused**

- Refresh tokens are **single-use only** and auto-rotated with each authentication request
- Each refresh invalidates the old token and returns a new one
- The `token_manager.py` automatically updates `config.json` with new refresh tokens
- Access tokens expire after 3600 seconds (1 hour)
- **The script should run every ~5 minutes** to keep the session alive and prevent token expiration
- If you don't rotate the refresh token regularly, it may expire and require re-extraction

---

## Alternative Token Extraction Methods

### Method 1: supabase.json File (Recommended)

The tokens are always stored in:

```bash
~/Library/Application Support/Granola/supabase.json
```

This file contains:
- `workos_tokens` - A JSON string (escaped) containing `refresh_token`, `access_token`, and other auth data
- `session_id` - Current session ID
- `user_info` - User profile information

### Method 2: Browser Developer Tools

For web-based authentication flows.

**Chrome:**

```bash
# Open Chrome Developer Tools (Cmd+Option+I)
# Navigate to: https://app.granola.ai
# Network tab > Filter: authenticate or workos
# Locate authentication response containing tokens
```

---

## Configuration

**Create configuration file:**

```bash
cp config.json.template config.json
```

**Edit config.json:**

```json
{
  "refresh_token": "<refresh-token-from-supabase.json>",
  "client_id": "client_<REDACTED>"
}
```

---

## Verification

**Test token validity:**

```bash
python3 main.py /path/to/output
```

**Expected output:**

```
Successfully obtained access token (expires in 3600 seconds)
```

---

## Common Issues

**Token already exchanged:**

- The refresh token was already used and is now invalid
- Extract a fresh refresh token from `supabase.json` (requires logging into Granola again)
- Update `config.json` with the new token

**Invalid grant:**

- Token expired or revoked
- Re-authenticate to Granola and extract new token from `supabase.json`
- Follow Step 3 to preserve your session

**Missing client_id:**

- Verify `config.json` contains both `refresh_token` and `client_id`
- Extract `client_id` from the JWT token in `supabase.json` as shown above

**Session keeps expiring:**

- Make sure you're refreshing the token every ~5 minutes
- Verify you removed the `~/Library/Application Support/Granola/` directory after extraction
- Check that `token_manager.py` is saving the new refresh token to `config.json`

