# Claude Code Guidelines

> Pointer file for AI assistants. Not documentation itself.

## Documentation

All documentation lives in `docs/`:

| File | Purpose |
|------|---------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, software architecture |
| [PROCEDURES.md](docs/PROCEDURES.md) | Operating workflows, CLI commands, dev setup |
| [STATISTICS-REFERENCE.md](docs/STATISTICS-REFERENCE.md) | All 35+ statistics categories with code |

## Project Structure

```
src/fplstats/          # Core Python package
  analyzers.py         # LeagueAnalyzer (40+ methods, main logic)
  models.py            # Pydantic data models
  enums.py             # Chip, Position enums
src/scripts/           # CLI entry points
  fetch_league.py      # FPL API data fetcher
  analyze_league.py    # Statistics generator
```

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
```

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

1. **Fetch data**: `python scripts/fetch_league.py --league=1026627 --email=... --cookie=...`
2. **Analyze**: `python scripts/analyze_league.py --season=2024_2025 --league=1026627`
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
