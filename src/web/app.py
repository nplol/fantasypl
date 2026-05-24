"""
Local Flask app that serves a dashboard of LeagueAnalyzer statistics.

Run directly:
    cd src && source env/bin/activate
    python -m web.app                       # or `flask --app web.app run -p 5000`

Caddy reverse-proxies localhost:8080 -> localhost:5000 (see Caddyfile).

Endpoints:
    GET /                                 → dashboard HTML
    GET /api/seasons                      → [{season, leagues:[{league_id, name}]}, ...]
    GET /api/stats/<season>/<league_id>   → {meta, sections: [{title, subtitle, rows}, ...]}
"""
from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import Flask, abort, jsonify, render_template
from pydantic import BaseModel
from werkzeug.middleware.proxy_fix import ProxyFix

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# LeagueAnalyzer uses relative paths like `data/<season>/<league_id>`,
# so we need to be cwd'd into src/ for it to find anything.
os.chdir(SRC_DIR)

from fplstats.analyzers import LeagueAnalyzer  # noqa: E402

# Section metadata mirrored from scripts/analyze_league.py:get_all_statistics().
# Source of truth lives in the CLI for now — if you add a new section there,
# add it here too. Drift is caught by visual inspection (no test bench yet).
STAT_SECTIONS: List[Dict[str, str]] = [
    {"title": "ÅRETS VISJONÆRE", "subtitle": "What if-tabell for GW1-picks", "method": "get_gw1_picks_standings"},
    {"title": "ÅRETS CAPTAIN FORESIGHT", "subtitle": "Spillerne med flest kapteinspoeng", "method": "get_captain_foresight"},
    {"title": "ÅRETS CAPTAIN HINDSIGHT", "subtitle": "Spillerne med flest poeng UTEN kapteinspoeng", "method": "get_captain_hindsight"},
    {"title": "ÅRETS LENGSTE LEDER", "subtitle": "Spillerne som har ledet ligaen flest gameweeks", "method": "get_longest_leader"},
    {"title": "ÅRETS LENGSTE BALLETAK", "subtitle": "Spillerne som har vært på sisteplass i ligaen flest gameweeks", "method": "get_longest_loser"},
    {"title": "ÅRETS STØRSTE LEDER", "subtitle": "Lagene som har ledet med flest poeng ligaen", "method": "get_biggest_leader"},
    {"title": "ÅRETS STØRSTE BALLETAK", "subtitle": "Lagene som har ligget bakerst med flest poeng ligaen", "method": "get_biggest_loser"},
    {"title": "ÅRETS GULLSTØVEL", "subtitle": "Spillerne som har scoret flest mål", "method": "get_top_scorers"},
    {"title": "ÅRETS ASSISTKONGE", "subtitle": "Spillerne som har flest assists", "method": "get_assist_kings"},
    {"title": "ÅRETS MÅLRETTEDE", "subtitle": "Spillerne som har flest mål+assists", "method": "get_most_goal_involvements"},
    {"title": "ÅRETS FORSVARSLØSE", "subtitle": "Spillerne som har flest mål imot fra spillende keepere og forsvarere", "method": "get_most_goals_conceded"},
    {"title": "ÅRETS SKUDDSIKRE", "subtitle": "Spillerne som har flest clean sheets fra spillende keepere og forsvarere", "method": "get_most_clean_sheets"},
    {"title": "ÅRETS KEEPER", "subtitle": "Spillerne som har flest strafferedninger", "method": "get_most_penalties_saved"},
    {"title": "ÅRETS FORMSPILLER", "subtitle": "Spillerne med høyest total ila. fem etterfølgende runder", "method": "get_best_streaks"},
    {"title": "ÅRETS UTE-AV-FORMSPILLER", "subtitle": "Spillerne med lavest total ila. fem etterfølgende runder", "method": "get_worst_streaks"},
    {"title": "ÅRETS STABILE", "subtitle": "Minst differanse mellom beste og verste GW", "method": "get_most_stable_user"},
    {"title": "ÅRETS BENKESLITER", "subtitle": "Spillerne med mest poeng på benken (eksklusiv autoinnbyttere)", "method": "get_most_bench_points"},
    {"title": "ÅRETS SUPERINNBYTTER", "subtitle": "Spillerne med mest autoinnbytterpoeng", "method": "get_most_auto_sub_points"},
    {"title": "ÅRETS STYGGE SPILLER", "subtitle": "Spillerne med flest minuspoeng for rødt+gult kort (fra spillende spillere)", "method": "get_most_cards"},
    {"title": "ÅRETS SELVEIDE", "subtitle": "Spillerne med flest selvmål", "method": "get_most_own_goals"},
    {"title": "ÅRETS BOMSPILLER", "subtitle": "Spillerne med flest straffebom", "method": "get_most_penalties_missed"},
    {"title": "ÅRETS BONUSSPILLER", "subtitle": "Spillerne med flest bonuspoeng", "method": "get_most_bonus_points"},
    {"title": "ÅRETS MVP", "subtitle": "Spillerne som har gitt mest poeng til et lag ila. sesongen, inklusive kapteinspoeng", "method": "get_most_points_by_player"},
    {"title": "ÅRETS BESTE DIFF (totalt)", "subtitle": "Differentials sortert på totale diff-poeng (max ownership 0.3)", "method": "get_best_differential", "tuple_index": 0},
    {"title": "ÅRETS BESTE DIFF (snitt)", "subtitle": "Differentials sortert på diff-poeng i snitt per runde", "method": "get_best_differential", "tuple_index": 1},
    {"title": "ÅRETS BESTE DIFF (én runde)", "subtitle": "Differentials sortert på beste enkeltrunde", "method": "get_best_differential", "tuple_index": 2},
    {"title": "ÅRETS HØYESTE RANK", "subtitle": "Spillerne med høyest gw+overall rank", "method": "get_highest_rank"},
    {"title": "ÅRETS LAVESTE RANK", "subtitle": "Spillerne med lavest gw+overall rank", "method": "get_lowest_rank"},
    {"title": "ÅRETS TEMPLATE", "subtitle": "Managerne med likest lag som de andre (i snitt per spiller per gameweek)", "method": "get_template_percentage"},
    {"title": "ÅRETS VINGLEPETTER", "subtitle": "Managerne som har vært innom flest plasser på tabellen", "method": "get_most_league_positions"},
    {"title": "ÅRETS CHIPP-KONGE", "subtitle": "Mest poeng på chips", "method": "get_most_chip_points"},
    {"title": "ÅRETS PIMP", "subtitle": "Mest hits, best hits (samme gameweek)", "method": "get_most_hits"},
    {"title": "ÅRETS HIGHSCORE", "subtitle": "Mest poeng på én gameweek", "method": "get_most_gw_points"},
    {"title": "ÅRETS LOWSCORE", "subtitle": "Lavest poeng på én gameweek", "method": "get_least_gw_points"},
    {"title": "ÅRETS RUNDBRENNER", "subtitle": "Managerne som har vært innom flest unike spillere", "method": "get_most_distinct_players"},
    {"title": "ÅRETS SPÅMANN", "subtitle": "Mest poeng fra spillere byttet inn samme runde", "method": "get_best_transfers"},
    {"title": "ÅRETS KARMA", "subtitle": "Mest poeng fra spillere byttet UT samme runde", "method": "get_worst_transfers"},
    {"title": "ÅRETS VANILLA (ICE)", "subtitle": "Vaniljepoeng: total ekskl. ekstra kapteinspoeng, auto-subs og benkespillere fra BB", "method": "get_vanilla_standings"},
]

# Friendly column labels — best-effort, falls back to the raw key if unmapped.
COLUMN_LABELS: Dict[str, str] = {
    "name": "Team",
    "user_name": "Team",
    "player_name": "Player",
    "team_name": "Team",
    "total_points": "Total points",
    "points": "Points",
    "total_captain_points": "Captain points",
    "total_vc_points": "VC points",
    "total_vice_captain_points": "VC points",
    "total_gameweeks_with_vc": "GWs with VC",
    "total_gameweeks_without_captain": "GWs no captain",
    "total_auto_sub_points": "Auto-sub points",
    "total_bench_points": "Bench points",
    "total_bonus_points": "Bonus points",
    "total_chip_points": "Chip points",
    "total_card_points": "Card points",
    "goals_scored": "Goals",
    "assists": "Assists",
    "goal_involvements": "Goal involvements",
    "goals_conceded": "Goals conceded",
    "clean_sheets": "Clean sheets",
    "penalties_saved": "Penalties saved",
    "penalties_missed": "Penalties missed",
    "own_goals": "Own goals",
    "yellow_cards": "Yellow cards",
    "red_cards": "Red cards",
    "first_place_count": "GWs in 1st",
    "last_place_count": "GWs in last",
    "point_gap": "Point gap",
    "gameweek": "GW",
    "event": "GW",
    "best_streak_total": "Best 5-GW total",
    "worst_streak_total": "Worst 5-GW total",
    "best_streak_start_gw": "Streak start GW",
    "worst_streak_start_gw": "Streak start GW",
    "best_streak_end_gw": "Streak end GW",
    "worst_streak_end_gw": "Streak end GW",
    "gw_diff": "GW spread",
    "best_gw": "Best GW",
    "worst_gw": "Worst GW",
    "best_gw_points": "Best GW points",
    "worst_gw_points": "Worst GW points",
    "highest_gw_rank": "Highest GW rank",
    "lowest_gw_rank": "Lowest GW rank",
    "highest_overall_rank": "Highest overall rank",
    "lowest_overall_rank": "Lowest overall rank",
    "template_percentage": "Template %",
    "template_share": "Template %",
    "distinct_league_positions": "Distinct positions",
    "league_positions": "Positions",
    "total_distinct_positions": "Distinct positions",
    "position_length": "Distinct positions",
    "total_players": "Distinct players",
    "distinct_players": "Players",
    "total_chip_points_excl_wc": "Chip points (no WC)",
    "total_wc_points": "Wildcard points",
    "max_diff_points": "Best GW diff",
    "max_diff_gameweek": "Best diff GW",
    "max_diff_ownership_share": "Best diff ownership",
    "gameweek_count": "Diff GW count",
    "avg_ownership_share": "Avg ownership",
    "extra_captain_points": "Extra captain points",
    "total_bbost_bench_points": "BB bench points",
    "total_vanilla_points": "Vanilla points",
    "total_hits": "Total hits",
    "best_hits_gameweek": "Best hits GW",
    "best_hits_points": "Best hits points",
    "gw_points": "GW points",
    "gw": "GW",
    "diff_points": "Diff points",
    "total_diff_points": "Total diff",
    "avg_diff_points": "Avg diff",
    "highest_diff_points": "Best single GW diff",
    "diff_gw": "Diff GW",
    "ownership_share": "Ownership",
    "player_points": "Player points",
    "transfer_in_points": "Transfer-in points",
    "transfer_out_points": "Transfer-out points",
    "total_transfer_points": "Transfer points",
    "vanilla_points": "Vanilla points",
    "captain_name": "Captain",
    "vice_captain_name": "Vice captain",
    "captain_vc_names": "Captain / VC",
    "gw1_player_names": "GW1 picks",
}

# Keys we never want to show — internal/foreign IDs and "detail blob" payloads
# that have a friendlier summary column right next to them.
HIDDEN_KEYS = {
    "id", "user_id", "player_id", "element",
    "distinct_players",  # huge list of player ids; total_players holds the count
    "gameweeks",  # per-GW breakdown blob in get_best_differential; not table-friendly
    "position_set",  # raw set of league positions; we have distinct_positions
}


def _normalize(value: Any) -> Any:
    """Recursively turn Pydantic / set / Enum / etc. into JSON-friendly primitives."""
    if isinstance(value, BaseModel):
        return _normalize(value.dict())
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        try:
            return sorted(_normalize(v) for v in value)
        except TypeError:
            return [_normalize(v) for v in value]
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, float):
        return round(value, 4)
    return value


def _columns_for(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Pick a stable, ordered column list from the first non-empty row.

    Drops keys in HIDDEN_KEYS, and any column whose first value is a
    list-of-dicts (too complex to render as a single cell)."""
    if not rows:
        return []
    first = next((r for r in rows if isinstance(r, dict)), None)
    if first is None:
        return []
    cols = []
    for key, value in first.items():
        if key in HIDDEN_KEYS:
            continue
        if isinstance(value, list) and value and isinstance(value[0], dict):
            continue
        cols.append({"key": key, "label": COLUMN_LABELS.get(key, key.replace("_", " ").title())})
    return cols


_ANALYZER_CACHE: Dict[Tuple[str, int], LeagueAnalyzer] = {}


def _get_analyzer(season: str, league_id: int) -> LeagueAnalyzer:
    key = (season, league_id)
    if key not in _ANALYZER_CACHE:
        _ANALYZER_CACHE[key] = LeagueAnalyzer(season, league_id, disable_prompt=True)
    return _ANALYZER_CACHE[key]


_STATS_CACHE: Dict[Tuple[str, int], Dict[str, Any]] = {}


def _build_stats(season: str, league_id: int) -> Dict[str, Any]:
    key = (season, league_id)
    if key in _STATS_CACHE:
        return _STATS_CACHE[key]

    analyzer = _get_analyzer(season, league_id)
    latest_gw = analyzer.get_latest_gameweek()

    sections: List[Dict[str, Any]] = []
    for section in STAT_SECTIONS:
        method_name = section["method"]
        method = getattr(analyzer, method_name, None)
        if method is None:
            continue
        try:
            raw = method(print_result=False)
            if "tuple_index" in section and isinstance(raw, tuple):
                raw = raw[section["tuple_index"]]
            normalized = _normalize(raw)
            rows = normalized if isinstance(normalized, list) else []
            sections.append({
                "title": section["title"],
                "subtitle": section["subtitle"],
                "method": method_name,
                "columns": _columns_for(rows),
                "rows": rows,
            })
        except Exception as exc:  # noqa: BLE001 — surfacing per-section failures, not crashing the whole page
            sections.append({
                "title": section["title"],
                "subtitle": section["subtitle"],
                "method": method_name,
                "columns": [],
                "rows": [],
                "error": f"{type(exc).__name__}: {exc}",
            })

    payload = {
        "meta": {
            "season": season,
            "league_id": league_id,
            "league_name": analyzer.league.name,
            "latest_gameweek": latest_gw.id,
            "latest_gameweek_finished": latest_gw.finished,
        },
        "sections": sections,
    }
    _STATS_CACHE[key] = payload
    return payload


def _discover_seasons() -> List[Dict[str, Any]]:
    """Walks src/data/<season>/<league_id>/league.json for everything cached."""
    data_root = SRC_DIR / "data"
    seasons: List[Dict[str, Any]] = []
    if not data_root.is_dir():
        return seasons
    for season_dir in sorted(data_root.iterdir()):
        if not season_dir.is_dir() or "_" not in season_dir.name:
            continue
        leagues: List[Dict[str, Any]] = []
        for league_dir in sorted(season_dir.iterdir()):
            if not league_dir.is_dir():
                continue
            league_json = league_dir / "league.json"
            if not league_json.exists():
                continue
            try:
                league_id = int(league_dir.name)
            except ValueError:
                continue
            try:
                import json
                with league_json.open() as fh:
                    league_name = json.load(fh).get("name", str(league_id))
            except Exception:
                league_name = str(league_id)
            leagues.append({"league_id": league_id, "name": league_name})
        if leagues:
            seasons.append({"season": season_dir.name, "leagues": leagues})
    return seasons


app = Flask(__name__)
# Behind the it-management Caddy on :9999, this app is served under /nplol/
# via `handle_path /nplol/* { reverse_proxy ... }` + `X-Forwarded-Prefix: /nplol`.
# ProxyFix reads that header into SCRIPT_NAME so url_for emits /nplol/static/...
# automatically. No-op when hit directly on :5000 (header absent).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/seasons")
def api_seasons():
    return jsonify(_discover_seasons())


@app.route("/api/stats/<season>/<int:league_id>")
def api_stats(season: str, league_id: int):
    try:
        return jsonify(_build_stats(season, league_id))
    except Exception as exc:  # noqa: BLE001
        abort(404, description=str(exc))


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
