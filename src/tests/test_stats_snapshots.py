"""
Snapshot regression tests for every public LeagueAnalyzer stat method.

For each (season, method) pair, we call the method with `print_result=False`,
normalize the return value, and assert it matches the snapshot on disk.

Regenerate snapshots intentionally with:
    pytest tests/test_stats_snapshots.py --update-snapshots
"""
import inspect

import pytest

from fplstats.analyzers import LeagueAnalyzer

from .conftest import SEASONS
from .snapshot import assert_matches_snapshot

# Methods that are pure helpers / orchestrators — not stats themselves.
EXCLUDED = {
    "print_result",
    "get_latest_gameweek",
    "get_player_gameweek_results",
    "get_combined_gameweek_result_for_player",
    "get_gameweek_players",
    "get_player_totals",
    "get_player_gameweek_ownership_share",
    "get_all_statistics",
}


def _stat_methods():
    """All public `get_*` methods on LeagueAnalyzer minus EXCLUDED."""
    methods = []
    for name, fn in inspect.getmembers(LeagueAnalyzer, predicate=inspect.isfunction):
        if not name.startswith("get_"):
            continue
        if name in EXCLUDED:
            continue
        methods.append(name)
    return sorted(methods)


STAT_METHODS = _stat_methods()


@pytest.mark.parametrize("season,league_id", SEASONS, ids=[s for s, _ in SEASONS])
@pytest.mark.parametrize("method_name", STAT_METHODS)
def test_stat_method_snapshot(
    season, league_id, method_name, analyzer_for, update_snapshots
):
    analyzer = analyzer_for(season, league_id)
    method = getattr(analyzer, method_name)

    # All stat methods accept print_result; pass it if supported so test output
    # stays clean. A few (e.g. get_latest_gameweek_number, get_historic_standings)
    # don't take it.
    sig = inspect.signature(method)
    if "print_result" in sig.parameters:
        result = method(print_result=False)
    else:
        result = method()

    assert_matches_snapshot(season, method_name, result, update=update_snapshots)


def test_analyzer_loads_all_seasons(analyzer_for):
    """Smoke test: every season's data parses cleanly into Pydantic models."""
    for season, league_id in SEASONS:
        a = analyzer_for(season, league_id)
        assert a.league.name
        assert len(a.users) > 0
        assert len(a.players) > 0
        assert a.get_latest_gameweek_number() > 0
