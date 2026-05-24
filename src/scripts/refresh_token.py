#!/usr/bin/env python3
"""
Headless FPL token refresh. See fplstats/fpl_auth.py for the full docstring.

Usage:
    python scripts/refresh_token.py --save-credentials   # first-time
    python scripts/refresh_token.py                       # headless refresh
    python scripts/refresh_token.py --force               # refresh even if valid

After a successful refresh, the token is in ~/.fpl/secrets.env:
    source ~/.fpl/secrets.env
    echo $FPL_X_API_AUTH
"""
import os
import sys

# Allow `import fplstats.*` from this scripts/ subdir, matching the pattern
# used by fetch_league.py / analyze_league.py.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fplstats.fpl_auth import main  # noqa: E402

if __name__ == "__main__":
    main()
