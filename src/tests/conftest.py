"""
Pytest config: chdir to src/ so analyzer's relative `data/...` paths resolve,
expose --update-snapshots, and cache one LeagueAnalyzer per season per session.
"""
import os
import sys

import pytest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SRC_DIR)
os.chdir(SRC_DIR)


# (season, league_id) pairs covered by the snapshot suite.
# Update here when adding a new season's data.
SEASONS = [
    ("2020_2021", 686617),
    ("2021_2022", 268207),
    ("2022_2023", 988260),
    ("2023_2024", 713444),
    ("2024_2025", 1026627),
]


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Overwrite snapshot files with current output instead of asserting.",
    )


@pytest.fixture(scope="session")
def update_snapshots(pytestconfig) -> bool:
    return pytestconfig.getoption("--update-snapshots")


_analyzer_cache: dict = {}


@pytest.fixture(scope="session")
def analyzer_for():
    """
    Returns a callable (season, league_id) -> LeagueAnalyzer.
    Cached for the session — parsing players.json is the slow part.
    """
    from fplstats.analyzers import LeagueAnalyzer

    def _get(season: str, league_id: int):
        key = (season, league_id)
        if key not in _analyzer_cache:
            _analyzer_cache[key] = LeagueAnalyzer(
                season, league_id, disable_prompt=True
            )
        return _analyzer_cache[key]

    return _get
