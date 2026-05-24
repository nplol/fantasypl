# Claude Code Guidelines

> Pointer file for AI assistants. Not documentation itself.

## Documentation

All documentation lives in `docs/`:

| File | Purpose |
|------|---------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, software architecture |
| [PROCEDURES.md](docs/PROCEDURES.md) | Operating workflows, CLI commands, dev setup |
| [STATISTICS-REFERENCE.md](docs/STATISTICS-REFERENCE.md) | All 35+ statistics categories with code |
| [HEADLESS-AUTH.md](docs/HEADLESS-AUTH.md) | One-time setup for the headless FPL token refresh (Playwright) |

## Project Structure

```
src/fplstats/          # Core Python package
  analyzers.py         # LeagueAnalyzer (40+ methods, main logic)
  models.py            # Pydantic data models
  enums.py             # Chip, Position enums
  fpl_auth.py          # Headless OAuth2 PKCE login via Playwright
src/scripts/           # CLI entry points
  fetch_league.py      # FPL API data fetcher
  analyze_league.py    # Statistics generator
  refresh_token.py     # Headless FPL token refresh
```

## Headless FPL auth

`src/fplstats/fpl_auth.py` drives Chromium through FPL's OAuth2 PKCE flow and captures the `X-Api-Authorization` JWT off the SPA's first authenticated `/api/` call. Python port of `fpl-ai-assist/fpl-mcp-server/scripts/refresh-token.ts` — same client_id, same `~/.fpl/credentials.env` + `~/.fpl/secrets.env` layout, so credentials are interchangeable across projects.

Full setup guide for a fresh machine: [docs/HEADLESS-AUTH.md](docs/HEADLESS-AUTH.md).

```bash
pip install -r requirements-auth.txt && playwright install chromium  # one-time
python scripts/refresh_token.py --save-credentials                    # first run
python scripts/refresh_token.py                                       # headless refresh
```

Programmatic use: `from fplstats.fpl_auth import get_valid_token`.

`scripts/fetch_league.py` hits the FPL public API directly via `fplstats.fpl_api` and works without a token for all cached/past data. Pass `--auth` (or `--fetch-live`) to attach a fresh token from `fpl_auth` — only needed for the in-flight gameweek before it locks.

## Code Style

- **Python 3.13** with virtual environment
- **Type hints everywhere** - use Pydantic models, generics, Optional
- **Naming**: snake_case (functions/vars), PascalCase (classes), UPPER_CASE (constants)
- **Imports**: stdlib → third-party → local, alphabetical within groups
- **Docstrings**: Simple, descriptive. No formal Args: sections needed
- **Private methods**: prefix with underscore `_method_name`

## Tooling

```bash
cd src && source env/bin/activate  # Always use venv

# Code quality (use defaults, no custom configs)
black .           # Format
isort .           # Sort imports
flake8 .          # Lint
mypy .            # Type check (uses mypy.ini with pydantic plugin)
pytest            # Run snapshot regression tests (~25s, 191 checks)
```

## Tests — snapshot regression bench

Lives in `src/tests/`. Auto-runs every public `get_*` method on `LeagueAnalyzer` against all 5 cached seasons and diffs against `tests/snapshots/{season}/{method}.json`.

```bash
pytest                         # verify nothing drifted
pytest -k 2024_2025            # one season (~2.5s)
pytest --update-snapshots      # regenerate after an intentional stat change
git diff tests/snapshots/      # ALWAYS review before committing regenerated snapshots
```

- New `get_*` methods are picked up automatically — no test wiring needed.
- Helpers/orchestrators are listed in `EXCLUDED` in `test_stats_snapshots.py`.
- See `src/tests/README.md` for the full workflow including known quirks (set non-determinism, embedded User bloat in transfer-related methods).
- Dev deps in `src/requirements-dev.txt` (pytest + deepdiff).

## Key Patterns

```python
# Pydantic models for all data structures
class UserResult(BaseModel):
    id: str
    name: str
    points: int

# Type-annotated methods with self-type
T = TypeVar("T", bound="LeagueAnalyzer")
def get_standings(self: T) -> List[Standing]: ...

# Caching pattern
if self._cached_value:
    return self._cached_value

# List comprehensions for filtering
finished = [gw for gw in self.gameweeks if gw.finished]
```

## Development Workflow

1. **Fetch data**: `python scripts/fetch_league.py --league=491678` (no creds needed for past GWs; add `--fetch-live` for the in-flight one)
2. **Analyze**: `python scripts/analyze_league.py --season=2025_2026 --league=491678`
3. **Output** goes to `statistics/` directory

## Commits

Use conventional commits format:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation
- `refactor:` code changes without behavior change

## Anti-patterns to Avoid

- Don't add unnecessary abstractions or helpers
- Don't add extensive error handling for internal code
- Don't modify formatting/style outside the changed code
- Don't add comments to self-explanatory code
- Output strings may be Norwegian - don't translate them

## Quick Reference

- **League ID**: 1026627 (nplol)
- **Data location**: `src/data/{season}/`
- **5 seasons of data**: 2020-2025
- **Rate limiting**: fetch_league.py has 4-second delays built in
