# Headless FPL auth

How to set up `src/fplstats/fpl_auth.py` on a fresh machine so you can refresh FPL auth tokens without manually pasting cookies from a browser.

## What this gives you

- A long-lived browser-driven login that runs on a headless server.
- A fresh `X-Api-Authorization` JWT saved to `~/.fpl/secrets.env`.
- Same credential/secret layout as [`fpl-ai-assist`](https://github.com/<user>/fpl-ai-assist) — if you've already set up that project, this one inherits the credentials automatically.

## What this does NOT do (yet)

- It does **not** update `scripts/fetch_league.py`. That script still uses the legacy `fpl` Python library and the email+cookie auth path. To fetch league data today, see the [src/README.md](../src/README.md) fetch instructions.
- Wiring the new token into `fetch_league.py` (so the fetch flow becomes fully headless) is a future migration. The plumbing is in place via `get_valid_token()`.

If you only need to fetch nplol data, you can probably skip this whole document — most of the FPL endpoints `fetch_league.py` hits are public and need no auth.

## One-time setup

```bash
# 1. From the repo root, enter the src venv (create it if missing)
cd src
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements-auth.txt   # adds playwright

# 2. Download the headless Chromium browser (~300 MB)
playwright install chromium

# 3. Save your FPL credentials (interactive — password input is hidden)
python scripts/refresh_token.py --save-credentials
```

After step 3 you'll have:

```
~/.fpl/credentials.env       chmod 0600   FPL_EMAIL / FPL_PASSWORD
```

## Refreshing the token

```bash
source env/bin/activate
python scripts/refresh_token.py            # no-op if current token is still valid
python scripts/refresh_token.py --force    # always refresh
```

This writes:

```
~/.fpl/secrets.env           chmod 0600   FPL_X_API_AUTH (Bearer JWT)
                                          FPL_MANAGER_ID (discovered from /api/me/)
```

Tokens last several hours. To use the token in a shell session:

```bash
source ~/.fpl/secrets.env
curl -H "X-Api-Authorization: $FPL_X_API_AUTH" \
     https://fantasy.premierleague.com/api/me/
```

## Using the token from Python

```python
import asyncio
from fplstats.fpl_auth import get_valid_token

token = asyncio.run(get_valid_token())   # refreshes if expired
headers = {
    "X-Api-Authorization": token,
    "User-Agent": "FPL-NPLOL-Stats/1.0",
}
```

## Storing the password in macOS Keychain instead of a plaintext file

The default `~/.fpl/credentials.env` is plaintext with `chmod 0600`. If you'd rather use macOS Keychain (so the password is never on disk in plaintext):

```bash
security add-generic-password -s 'fpl-email'    -a "$USER" -w '<your email>'
security add-generic-password -s 'fpl-password' -a "$USER" -w '<your password>'
```

Then in your code:

```python
from fplstats.fpl_auth import load_credentials_from_keychain, _drive_login

creds = load_credentials_from_keychain()    # reads from Keychain
token = await _drive_login(creds.email, creds.password)
```

Or delete `~/.fpl/credentials.env` after running `--save-credentials` once and patch the loader. The shipped default matches the TS reference for cross-project parity, not as a security recommendation.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'playwright'` | Missing optional deps | `pip install -r requirements-auth.txt` |
| `playwright._impl._errors.Error: Executable doesn't exist` | Chromium not downloaded | `playwright install chromium` |
| `no credentials found. Run: ... --save-credentials` | First-time setup not done | `python scripts/refresh_token.py --save-credentials` |
| `failed to capture token — login likely failed` | Wrong password OR FPL changed the login page selectors | Re-save credentials; if persistent, the email-field selector list in `fpl_auth.py:_drive_login` may need a new variant |
| `Unable to find a signing key that matches: ...` from `/api/me/` after refresh | Captured a DaVinci flow JWT, not a user token | Already guarded against in `is_user_access_token()` — if this fires, the FPL OAuth provider's token shape has changed and the guard needs updating |
| Token expires very quickly (< 1h) | Token captured before SPA finished login handshake | The fallback `goto(/my-team)` should prevent this; if not, raise the deadline in `_drive_login` |

## How it works

Same flow as the TS reference (`fpl-ai-assist/fpl-mcp-server/scripts/refresh-token.ts`):

1. Launch headless Chromium with a desktop User-Agent.
2. Generate PKCE code verifier/challenge and a random state.
3. Build the OAuth2 authorize URL directly (`account.premierleague.com/as/authorize`) — bypasses the SPA's login button which has redirect_uri issues in headless mode.
4. Fill email + password, submit.
5. After login the SPA reloads at `fantasy.premierleague.com` and makes authenticated `/api/` calls. A request listener captures the `X-Api-Authorization` header off the first such call.
6. Validate the captured JWT is a *user* access token (not one of DaVinci's flow-bootstrap JWTs that have `usage=startSpecificFlowOrPolicyNonUserContext` or `sub==aud`).
7. Hit `/api/me/` with the captured token to discover the manager id.
8. Save token + manager id to `~/.fpl/secrets.env`.

## Files

| Path | Purpose |
|---|---|
| `src/fplstats/fpl_auth.py` | Auth module — token lifecycle, PKCE, browser flow |
| `src/scripts/refresh_token.py` | CLI wrapper |
| `src/requirements-auth.txt` | Optional Playwright dep |
| `~/.fpl/credentials.env` | Your FPL email + password (chmod 0600) |
| `~/.fpl/secrets.env` | Refreshed token + manager id (chmod 0600) |
