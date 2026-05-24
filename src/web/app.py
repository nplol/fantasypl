"""
Local Flask app that serves a dashboard of LeagueAnalyzer statistics.

Run:
    cd src && source env/bin/activate
    python -m web.app                       # or `flask --app web.app run -p 5000`

Then open http://localhost:5000.

If you want to expose the dashboard under a path prefix behind a reverse
proxy (e.g. /nplol/), have the proxy send `X-Forwarded-Prefix: /nplol` —
ProxyFix below reads that into SCRIPT_NAME and url_for emits the right
URLs. Header is absent on direct hits, so localhost:5000 just works.

Endpoints:
    GET /                                 → dashboard HTML
    GET /api/seasons                      → [{season, leagues:[{league_id, name}]}, ...]
    GET /api/stats/<season>/<league_id>   → {meta, sections: [{title, subtitle, rows}, ...]}
"""
from __future__ import annotations

import os
import re
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
    "gameweek_number": "GW",
    "gameweek_points": "GW points",
    "gameweek_rank": "GW rank",
    "gw_diff": "GW spread",
    "best_gw": "Best GW",
    "worst_gw": "Worst GW",
    "best_gw_points": "Best GW points",
    "worst_gw_points": "Worst GW points",
    "highest_gw_rank": "Best GW rank",
    "lowest_gw_rank": "Worst GW rank",
    "highest_overall_rank": "Best overall rank",
    "lowest_overall_rank": "Worst overall rank",
    "highest_gw": "Best GW",
    "lowest_gw": "Worst GW",
    "highest_gw_rank_gw": "GW",
    "lowest_gw_rank_gw": "GW",
    "highest_overall_rank_gw": "GW",
    "lowest_overall_rank_gw": "GW",
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
    "squad": "GW1 squad",
}

# Keys we never want to show — internal/foreign IDs and "detail blob" payloads
# that have a friendlier summary column right next to them.
HIDDEN_KEYS = {
    "id", "user_id", "player_id", "element",
    "distinct_players",  # huge list of player ids; total_players holds the count
    "gameweeks",  # per-GW breakdown blob in get_best_differential; not table-friendly
    "position_set",  # raw set of league positions; we have distinct_positions
    "gw1_player_names",  # flat string; we replace it with a structured `squad` field
    # GW context for paired value columns — rendered as inline "@ GW N" suffix
    # on the paired value cell by the frontend. See SIBLING_GW_KEYS below.
    "highest_gw", "lowest_gw",
    "highest_gw_rank_gw", "lowest_gw_rank_gw",
    "highest_overall_rank_gw", "lowest_overall_rank_gw",
}

# Maps a value column key to the row key holding "what GW it happened on".
# The frontend reads this from `meta.sibling_gw_keys` to render the value
# cell as e.g. "91 @ GW33" — keeps tables narrow on mobile.
SIBLING_GW_KEYS: Dict[str, str] = {
    "highest_gw_points": "highest_gw",
    "lowest_gw_points": "lowest_gw",
    "highest_gw_rank": "highest_gw_rank_gw",
    "lowest_gw_rank": "lowest_gw_rank_gw",
    "highest_overall_rank": "highest_overall_rank_gw",
    "lowest_overall_rank": "lowest_overall_rank_gw",
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


# Column display priority. Lower number = further left. Keys without an entry
# fall to the middle (10) and otherwise keep their natural insertion order.
# Goal: on a narrow mobile column, the most important context is visible first.
COLUMN_PRIORITY: Dict[str, int] = {
    "name": 0, "user_name": 0, "team_name": 0,
    "player_name": 1,
    "gameweek_number": 2, "gameweek": 2, "event": 2, "gw": 2,
    "max_diff_gameweek": 3, "best_hits_gameweek": 3,
    "best_streak_start_gw": 3, "worst_streak_start_gw": 3,
    "best_gw": 3, "worst_gw": 3,
    # Pair-context: GW for highest/lowest score & rank stats. Each "GW" column
    # sits immediately to the LEFT of its sibling value column.
    "highest_gw": 4, "lowest_gw": 4,
    "highest_gw_rank_gw": 4, "lowest_gw_rank_gw": 4,
    "highest_overall_rank_gw": 4, "lowest_overall_rank_gw": 4,
    # everything else: 10
    "squad": 90,  # heavy column; push to the right of the table
}


def _columns_for(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Pick a stable, ordered column list from the first non-empty row.

    Drops keys in HIDDEN_KEYS, and any column whose first value is a
    list-of-dicts (too complex to render as a single cell). Reorders by
    COLUMN_PRIORITY so team-name + key context come first on narrow screens."""
    if not rows:
        return []
    first = next((r for r in rows if isinstance(r, dict)), None)
    if first is None:
        return []
    candidate: List[Tuple[int, int, str]] = []
    for i, (key, value) in enumerate(first.items()):
        if key in HIDDEN_KEYS:
            continue
        # `squad` is a list-of-dicts but we want to render it; let it through.
        if key != "squad" and isinstance(value, list) and value and isinstance(value[0], dict):
            continue
        candidate.append((COLUMN_PRIORITY.get(key, 10), i, key))
    candidate.sort()
    return [
        {"key": key, "label": COLUMN_LABELS.get(key, key.replace("_", " ").title())}
        for (_, _, key) in candidate
    ]


_POSITION_LABEL = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD", 5: "MGR"}
_POSITION_ORDER = [1, 2, 3, 4, 5]


def _user_gw_extremes(analyzer: "LeagueAnalyzer") -> Dict[str, Dict[str, Any]]:
    """For every user, find which GW produced their best/worst points and rank.

    Skips GWs with no live matches (gameweeks where highest_score == 0) and
    GWs that aren't finished yet (rank is None) — same filtering the analyzer
    uses in get_least_gw_points / get_most_gw_points."""
    out: Dict[str, Dict[str, Any]] = {}
    gameweeks_by_event = {g.id: g for g in analyzer.gameweeks}
    for uid, user in analyzer.users.items():
        best_pts = best_pts_gw = None
        worst_pts = worst_pts_gw = None
        best_gw_rank = best_gw_rank_gw = None
        worst_gw_rank = worst_gw_rank_gw = None
        best_overall_rank = best_overall_rank_gw = None
        worst_overall_rank = worst_overall_rank_gw = None
        for h in user.history:
            gw = gameweeks_by_event.get(h.event)
            if not gw or gw.highest_score == 0 or h.rank is None:
                continue
            if best_pts is None or h.points > best_pts:
                best_pts, best_pts_gw = h.points, h.event
            if worst_pts is None or h.points < worst_pts:
                worst_pts, worst_pts_gw = h.points, h.event
            if h.rank is not None and (best_gw_rank is None or h.rank < best_gw_rank):
                best_gw_rank, best_gw_rank_gw = h.rank, h.event
            if h.rank is not None and (worst_gw_rank is None or h.rank > worst_gw_rank):
                worst_gw_rank, worst_gw_rank_gw = h.rank, h.event
            if best_overall_rank is None or h.overall_rank < best_overall_rank:
                best_overall_rank, best_overall_rank_gw = h.overall_rank, h.event
            if worst_overall_rank is None or h.overall_rank > worst_overall_rank:
                worst_overall_rank, worst_overall_rank_gw = h.overall_rank, h.event
        out[uid] = {
            "best_pts_gw": best_pts_gw,
            "worst_pts_gw": worst_pts_gw,
            "best_gw_rank_gw": best_gw_rank_gw,
            "worst_gw_rank_gw": worst_gw_rank_gw,
            "best_overall_rank_gw": best_overall_rank_gw,
            "worst_overall_rank_gw": worst_overall_rank_gw,
        }
    return out


def _insert_after(row: Dict[str, Any], anchor_key: str, new_key: str, value: Any) -> Dict[str, Any]:
    """Returns a copy of `row` with `new_key` inserted immediately after `anchor_key`."""
    new: Dict[str, Any] = {}
    for k, v in row.items():
        new[k] = v
        if k == anchor_key:
            new[new_key] = value
    if new_key not in new:
        new[new_key] = value
    return new


def _augment_stable(rows: List[Dict[str, Any]], extremes: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        uid = row.get("user_id") or row.get("id")
        e = extremes.get(uid, {}) if uid else {}
        r = _insert_after(row, "highest_gw_points", "highest_gw", e.get("best_pts_gw"))
        r = _insert_after(r, "lowest_gw_points", "lowest_gw", e.get("worst_pts_gw"))
        out.append(r)
    return out


def _augment_highest_rank(rows: List[Dict[str, Any]], extremes: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        uid = row.get("user_id") or row.get("id")
        e = extremes.get(uid, {}) if uid else {}
        r = _insert_after(row, "highest_gw_rank", "highest_gw_rank_gw", e.get("best_gw_rank_gw"))
        r = _insert_after(r, "highest_overall_rank", "highest_overall_rank_gw", e.get("best_overall_rank_gw"))
        out.append(r)
    return out


def _augment_lowest_rank(rows: List[Dict[str, Any]], extremes: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        if not isinstance(row, dict):
            out.append(row)
            continue
        uid = row.get("user_id") or row.get("id")
        e = extremes.get(uid, {}) if uid else {}
        r = _insert_after(row, "lowest_gw_rank", "lowest_gw_rank_gw", e.get("worst_gw_rank_gw"))
        r = _insert_after(r, "lowest_overall_rank", "lowest_overall_rank_gw", e.get("worst_overall_rank_gw"))
        out.append(r)
    return out


def _augment_gw1_picks(rows: List[Dict[str, Any]], analyzer: "LeagueAnalyzer") -> List[Dict[str, Any]]:
    """Rebuilds the GW1 squad string into a structured array sorted GK→DEF→MID→FWD.

    The analyzer returns `gw1_player_names` as a single flat string with newlines
    between position groups. We pull the per-player season-long "what-if" totals
    out of that string by regex (`(NN)` after each name) and zip them back onto
    each user's raw GW1 picks from analyzer.users[uid].history[0].picks. This
    guarantees position-sorted output regardless of the order FPL returns picks
    in, and gives the frontend a structured payload to render."""
    new_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            new_rows.append(row)
            continue
        uid = row.get("user_id")
        squad: List[Dict[str, Any]] = []
        user = analyzer.users.get(uid) if uid else None
        if user and user.history and user.history[0].picks:
            picks = user.history[0].picks
            # Only digit-bearing parens get matched; "(C)"/"(VC)" are skipped.
            points_list = [int(m) for m in re.findall(r"\((\d+)\)", row.get("gw1_player_names") or "")]
            if len(points_list) < len(picks):
                points_list = points_list + [0] * (len(picks) - len(points_list))

            starters_by_pos: Dict[int, List[Dict[str, Any]]] = {p: [] for p in _POSITION_ORDER}
            bench: List[Dict[str, Any]] = []
            for i, pick in enumerate(picks):
                player = analyzer.players.get(pick.element)
                if not player:
                    continue
                cap = "(C)" if pick.is_captain else "(VC)" if pick.is_vice_captain else ""
                entry = {
                    "name": player.web_name,
                    "captain": cap,
                    "points": points_list[i] if i < len(points_list) else 0,
                }
                pos_val = player.element_type.value  # Enum -> int (1..5)
                if i < 11:
                    starters_by_pos.setdefault(pos_val, []).append(entry)
                else:
                    bench.append(entry)

            for pos in _POSITION_ORDER:
                if starters_by_pos.get(pos):
                    squad.append({"pos": _POSITION_LABEL[pos], "players": starters_by_pos[pos]})
            if bench:
                squad.append({"pos": "Bench", "players": bench})

        # Rebuild the row preserving column order; substitute gw1_player_names -> squad.
        new_row: Dict[str, Any] = {}
        inserted = False
        for k, v in row.items():
            if k == "gw1_player_names":
                new_row["squad"] = squad
                inserted = True
            else:
                new_row[k] = v
        if not inserted:
            new_row["squad"] = squad
        new_rows.append(new_row)
    return new_rows


# Substring-based team tagging. Lowercase substring match against team_name
# handles variants like "Redlightning" vs "Red Lightning" across seasons, and
# curly vs straight apostrophes in "Soccer MC's".
TEAM_PILL_RULES: List[Tuple[str, str]] = [
    ("redlight", "YouTube"),
    ("red lightning", "YouTube"),
    ("soccer mc", "YouTube"),
    ("pc bears", "YouTube"),
    ("sisteplass", "YouTube"),
    ("siste plass", "YouTube"),
    ("midten", "AI"),
]


def _pills_for_team(name: str) -> List[str]:
    name_l = (name or "").lower()
    pills: List[str] = []
    for sub, label in TEAM_PILL_RULES:
        if sub in name_l and label not in pills:
            pills.append(label)
    return pills


def _team_tags(analyzer: "LeagueAnalyzer") -> Dict[str, Dict[str, Any]]:
    """Returns {user_id: {place, name, pills}} from final league standings."""
    tags: Dict[str, Dict[str, Any]] = {}
    for s in analyzer.league.standings:
        tags[s.entry] = {
            "place": s.rank,
            "name": s.entry_name,
            "pills": _pills_for_team(s.entry_name),
        }
    return tags


_ANALYZER_CACHE: Dict[Tuple[str, int], LeagueAnalyzer] = {}
_STATS_CACHE: Dict[Tuple[str, int], Dict[str, Any]] = {}
# Cached mtime per (season, league) so we can invalidate when fetch_league
# rewrites the JSON. users.json is the heaviest file rewritten on every fetch.
_CACHE_MTIME: Dict[Tuple[str, int], float] = {}


def _data_mtime(season: str, league_id: int) -> float:
    """Returns the newest mtime across the source files for a league.

    If any of these files has been rewritten (e.g. by fetch_league.py), the
    cached analyzer + stats are stale and need to be rebuilt."""
    base = SRC_DIR / "data" / season / str(league_id)
    paths = [base / "users.json", base / "players.json", base / "gameweeks.json", base / "league.json"]
    newest = 0.0
    for p in paths:
        try:
            m = p.stat().st_mtime
            if m > newest:
                newest = m
        except OSError:
            pass
    return newest


def _invalidate_if_stale(key: Tuple[str, int]) -> None:
    season, league_id = key
    current = _data_mtime(season, league_id)
    cached = _CACHE_MTIME.get(key)
    if cached is not None and current > cached:
        _ANALYZER_CACHE.pop(key, None)
        _STATS_CACHE.pop(key, None)
        _CACHE_MTIME.pop(key, None)


def _get_analyzer(season: str, league_id: int) -> LeagueAnalyzer:
    key = (season, league_id)
    _invalidate_if_stale(key)
    if key not in _ANALYZER_CACHE:
        _ANALYZER_CACHE[key] = LeagueAnalyzer(season, league_id, disable_prompt=True)
        _CACHE_MTIME[key] = _data_mtime(season, league_id)
    return _ANALYZER_CACHE[key]


def _build_stats(season: str, league_id: int) -> Dict[str, Any]:
    key = (season, league_id)
    _invalidate_if_stale(key)
    if key in _STATS_CACHE:
        return _STATS_CACHE[key]

    analyzer = _get_analyzer(season, league_id)
    latest_gw = analyzer.get_latest_gameweek()
    extremes = _user_gw_extremes(analyzer)

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
            if method_name == "get_gw1_picks_standings":
                rows = _augment_gw1_picks(rows, analyzer)
            elif method_name == "get_most_stable_user":
                rows = _augment_stable(rows, extremes)
            elif method_name == "get_highest_rank":
                rows = _augment_highest_rank(rows, extremes)
            elif method_name == "get_lowest_rank":
                rows = _augment_lowest_rank(rows, extremes)
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
            "team_tags": _team_tags(analyzer),
            "sibling_gw_keys": SIBLING_GW_KEYS,
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
# Make Flask cooperate with an upstream reverse proxy: ProxyFix reads
# X-Forwarded-Prefix into SCRIPT_NAME so url_for emits the right path
# (`/nplol/static/...` instead of `/static/...`) when mounted under a prefix.
# No-op when the header is absent — direct hits on :5000 still work.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.context_processor
def _inject_asset_version() -> Dict[str, str]:
    """File-mtime cache buster for static assets — phones cache JS aggressively."""
    static_dir = Path(app.static_folder or "static")
    try:
        mtimes = [(static_dir / f).stat().st_mtime for f in ("app.js", "style.css")]
        return {"asset_v": str(int(max(mtimes)))}
    except (FileNotFoundError, OSError):
        return {"asset_v": "0"}


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
