# Test bench

Snapshot regression tests for `LeagueAnalyzer`. Goal: catch *any* numeric drift when adding new stats or refactoring existing ones.

## How it works

For each public `get_*` method on `LeagueAnalyzer` and each of the 5 archived seasons, we:

1. Call the method with `print_result=False`.
2. Normalize the return value to JSON-safe data (Pydantic → dict, set → sorted list, float → 10 decimals).
3. Compare against `tests/snapshots/{season}/{method_name}.json`.

On mismatch, the failure shows a `deepdiff` summary of exactly what changed — not a wall of JSON.

## Running

From `src/` (with the venv active):

```bash
pytest                                      # full suite (~25s)
pytest -k 2024_2025                         # one season (~2.5s)
pytest -k get_top_scorers                   # one method, all seasons
pytest tests/test_stats_snapshots.py -x     # stop on first failure
```

## When a stat genuinely changes

Regenerate snapshots, then re-run to verify:

```bash
pytest --update-snapshots
pytest                                      # confirm clean pass
git diff tests/snapshots/                   # review what changed
```

Review the diff before committing — `--update-snapshots` accepts whatever the code produces now, so a buggy commit would silently rewrite the golden truth.

## Adding a new stat method

1. Add the method to `LeagueAnalyzer`. It must return a JSON-serializable value (lists, dicts, Pydantic models, primitives).
2. Run `pytest --update-snapshots`. The new method is auto-picked up via `inspect.getmembers`.
3. Eyeball the new snapshot files in `tests/snapshots/{season}/{your_method}.json`.
4. Commit.

To exclude a method (helpers, orchestrators), add its name to `EXCLUDED` in `test_stats_snapshots.py`.

## Adding a new season

Edit `SEASONS` in `tests/conftest.py`, ensure `data/{season}/{league_id}/` exists, then `pytest --update-snapshots`.

## Known quirks

- **Snapshot bloat:** A few methods (`get_most_hits`, `get_best_transfers`, `get_worst_transfers`) return the full `User` Pydantic object embedded in each row, so their snapshots are 1-2 MB each. Total fixture size is ~16 MB. If the `User` model gains/loses fields, those snapshots need regenerating even though no calculation logic changed.
- **Non-determinism:** Two methods return Python `set`s (`get_most_distinct_players`, `get_most_league_positions`). The snapshot helper sorts them for stability. If you add a method that returns a set, this is already handled.
- **`disable_prompt=True`:** Fixtures always pass this. Don't add interactive prompts to new methods unless they're gated behind the flag.
- **`live=False`:** Fixtures default to historical (finished-only) mode. Add a separate test if a method behaves differently under `live=True`.
