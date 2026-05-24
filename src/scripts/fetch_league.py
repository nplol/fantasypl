#!/usr/bin/env python3
"""
Fetch FPL mini-league data using the new token-based API client.

Replaces the legacy `fpl` Python library which has been unreliable since FPL
migrated to OAuth2 PKCE auth. Talks to fantasy.premierleague.com/api directly
via FPLApiClient (src/fplstats/fpl_api.py), with optional token auth from
fpl_auth.get_valid_token().

Most endpoints used here are public — auth is only required if you want to
fetch live/in-flight gameweek data (picks before the gameweek locks). Past
seasons and finished gameweeks work without any auth.

Usage:
    python scripts/fetch_league.py --league=<id>
    python scripts/fetch_league.py --league=<id> --force-fetch-all
    python scripts/fetch_league.py --league=<id> --fetch-live    # needs auth
    python scripts/fetch_league.py --league=<id> --auth           # use token even for past data

Output JSON files (data/<season>/<league_id>/):
    league.json      — league info + standings
    gameweeks.json   — events array from bootstrap-static
    user_list.json   — flat list of users in the league
    users.json       — per-user history, picks, auto_subs, chips, transfers
    players.json     — bootstrap-static elements merged with element-summary
                       (history, fixtures, history_past) per touched player
"""
import argparse
import asyncio
import json
import os
import pathlib
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

# Allow `import fplstats.*` from this scripts/ subdir.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fplstats.fpl_api import FPLApiClient, FPLApiError  # noqa: E402

LEAGUE_FILE_NAME = "league"
GAMEWEEKS_FILE_NAME = "gameweeks"
USER_LIST_FILE_NAME = "user_list"
USERS_FILE_NAME = "users"
PLAYERS_FILE_NAME = "players"

# Rate limits — be a good API citizen.
USER_SLEEP_SECONDS = 4    # between full user fetches (matches legacy behaviour)
SUBCALL_SLEEP_SECONDS = 0.5
PLAYER_SLEEP_SECONDS = 1.5


def _path(base: str, file_name: str) -> str:
    return os.path.join(base, f"{file_name}.json")


def _read_file(base: str, file_name: str) -> Optional[Any]:
    try:
        with open(_path(base, file_name)) as f:
            return json.load(f)
    except IOError:
        return None


def _write_file(base: str, file_name: str, obj: Any) -> None:
    path = _path(base, file_name)
    print(f"  -> writing {path}")
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def _empty_history_for_late_joiner(gw_number: int) -> Dict[str, Any]:
    """
    Stub history entry for managers who joined the league after GW1.
    Matches the shape produced by the legacy fpl library so the analyzer
    can iterate user.history[i] without IndexError.
    """
    return {
        "event": gw_number,
        "points": 0,
        "total_points": 0,
        "rank": 9158154,
        "rank_sort": 9158154,
        "overall_rank": 9158154,
        "percentile_rank": None,
        "bank": 0,
        "value": 1000,
        "event_transfers": 0,
        "event_transfers_cost": 0,
        "points_on_bench": 0,
        "picks": [],
        "auto_subs": [],
        "chips": [],
        "transfers": [],
    }


def _missing_gameweeks(
    cached_user: Optional[Dict[str, Any]], finished_gameweeks: List[int]
) -> List[int]:
    """Return finished gameweeks where the cached user has no picks yet."""
    if not cached_user:
        return list(finished_gameweeks)
    cached_picks_by_gw = {
        h["event"]: bool(h.get("picks"))
        for h in cached_user.get("history", [])
        if h.get("event")
    }
    return [gw for gw in finished_gameweeks if not cached_picks_by_gw.get(gw)]


async def _build_user_data(
    api: FPLApiClient,
    user_entry: Dict[str, Any],
    finished_gameweeks: List[int],
    element_type_by_id: Dict[int, int],
    cached_user: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Returns a User dict in the JSON shape the analyzer expects.

    If `cached_user` is provided, only fetches picks for gameweeks not already
    in the cache. History, chips, and transfers are always refreshed (single
    cheap call each).
    """
    entry_id = int(user_entry["id"])
    user: Dict[str, Any] = {**user_entry}

    missing = _missing_gameweeks(cached_user, finished_gameweeks)
    cached_history_by_gw: Dict[int, Dict[str, Any]] = {
        h["event"]: h for h in (cached_user.get("history", []) if cached_user else [])
        if h.get("event")
    }
    if cached_user and not missing:
        print(f"\t\tcached through gw{finished_gameweeks[-1]} — refreshing history/transfers only")

    # 1. history endpoint — gives `current` (per-gw), `chips`, `past`.
    history_resp = await api.get_entry_history(entry_id)
    await asyncio.sleep(SUBCALL_SLEEP_SECONDS)
    current_history: List[Dict[str, Any]] = list(history_resp.get("current", []))
    chips_root: List[Dict[str, Any]] = list(history_resp.get("chips", []))

    # Insert empty stubs for any gameweeks before the manager's first one.
    if current_history:
        first_event = current_history[0]["event"]
        if first_event > 1:
            stubs = [_empty_history_for_late_joiner(gw) for gw in range(1, first_event)]
            current_history = stubs + current_history
            print(
                f"\t\t(added {len(stubs)} empty stub gameweeks — manager joined at GW{first_event})"
            )

    # Default the denormalized per-gw lists.
    for gw_entry in current_history:
        gw_entry.setdefault("auto_subs", [])
        gw_entry.setdefault("chips", [])
        gw_entry.setdefault("transfers", [])
        gw_entry.setdefault("picks", [])

    # 2. picks endpoint — only for gameweeks we don't have cached picks for.
    auto_subs_root: List[Dict[str, Any]] = []
    if missing:
        print(f"\t\tfetching picks for gw{missing}")

    for gw_number in finished_gameweeks:
        gw_index = gw_number - 1
        if gw_index >= len(current_history):
            continue

        # Copy cached picks/auto_subs if available and not in the missing list.
        if gw_number not in missing and gw_number in cached_history_by_gw:
            cached_gw = cached_history_by_gw[gw_number]
            current_history[gw_index]["picks"] = list(cached_gw.get("picks", []))
            for sub in cached_gw.get("auto_subs", []):
                current_history[gw_index]["auto_subs"].append(sub)
                auto_subs_root.append(sub)
            continue

        try:
            picks_resp = await api.get_entry_picks(entry_id, gw_number)
        except FPLApiError as e:
            # Picks before a manager joins, or before GW1 deadline, can 404.
            if e.status == 404:
                continue
            raise

        # Augment picks with `element_type` to match the legacy fpl shape.
        picks = []
        for pick in picks_resp.get("picks", []):
            element_id = int(pick["element"])
            picks.append({**pick, "element_type": element_type_by_id.get(element_id)})
        current_history[gw_index]["picks"] = picks

        # Auto-subs are attached to the picks endpoint.
        for sub in picks_resp.get("automatic_subs", []):
            current_history[gw_index]["auto_subs"].append(sub)
            auto_subs_root.append(sub)

        await asyncio.sleep(SUBCALL_SLEEP_SECONDS)

    # 3. chips — already obtained from history_resp; denormalize per-gw.
    for chip in chips_root:
        gw_index = chip["event"] - 1
        if 0 <= gw_index < len(current_history):
            current_history[gw_index]["chips"].append(chip)

    # 4. transfers
    transfers_root = await api.get_entry_transfers(entry_id)
    await asyncio.sleep(SUBCALL_SLEEP_SECONDS)
    for transfer in transfers_root:
        gw_index = transfer["event"] - 1
        if 0 <= gw_index < len(current_history):
            current_history[gw_index]["transfers"].append(transfer)

    user["history"] = current_history
    user["auto_subs"] = auto_subs_root
    user["chips"] = chips_root
    user["transfers"] = transfers_root
    return user


async def _merge_player_summary(api: FPLApiClient, base_element: Dict[str, Any]) -> Dict[str, Any]:
    """Merge bootstrap-static element with element-summary (history/fixtures/history_past)."""
    summary = await api.get_element_summary(int(base_element["id"]))
    merged = {**base_element}
    merged["history"] = summary.get("history", [])
    merged["fixtures"] = summary.get("fixtures", [])
    merged["history_past"] = summary.get("history_past", [])
    return merged


async def fetch_league_data(  # noqa: C901
    league_id: int,
    *,
    force_fetch_all: bool = False,
    fetch_live: bool = False,
    use_auth: bool = False,
) -> None:
    print(f"Fetching data for league {league_id} (force_fetch_all={force_fetch_all}, fetch_live={fetch_live})\n")

    # Acquire token if asked (or required by fetch_live).
    token: Optional[str] = None
    if use_auth or fetch_live:
        from fplstats.fpl_auth import get_valid_token
        print("Acquiring FPL auth token via fpl_auth...")
        token = await get_valid_token()
        print(f"  token acquired ({len(token)} chars)")
        print()

    async with FPLApiClient(token=token) as api:
        # 1. League info + standings
        print(f"Fetching league {league_id} standings...")
        league_resp = await api.get_classic_league_standings(league_id)
        league_info = league_resp.get("league", {})
        standings_raw = league_resp.get("standings", {}).get("results", [])
        print(f"  league: {league_info.get('name')}  ({len(standings_raw)} entries)")

        league_created = league_info.get("created") or ""
        try:
            league_created_year = int(league_created[0:4])
            season = f"{league_created_year}_{league_created_year + 1}"
        except (ValueError, IndexError):
            raise SystemExit(
                f"Could not derive season from league.created='{league_created}'. "
                f"League may not exist or response shape changed."
            )
        print(f"  season: {season}")

        base_data_path = f"data/{season}/{league_id}"
        pathlib.Path(base_data_path).mkdir(parents=True, exist_ok=True)

        league_data = {**league_info, "standings": standings_raw}
        _write_file(base_data_path, LEAGUE_FILE_NAME, league_data)

        # 2. User list
        user_list = [
            {"id": s["entry"], "name": s["entry_name"], "player_name": s["player_name"]}
            for s in standings_raw
        ]
        _write_file(base_data_path, USER_LIST_FILE_NAME, user_list)
        print(f"  user_list: {len(user_list)} users")

        # 3. Bootstrap-static — gives us gameweeks + element catalog
        print("\nFetching bootstrap-static...")
        bootstrap = await api.get_bootstrap_static()
        gameweeks = bootstrap.get("events", [])
        elements_index: Dict[int, Dict[str, Any]] = {
            int(e["id"]): e for e in bootstrap.get("elements", [])
        }
        element_type_by_id = {pid: e["element_type"] for pid, e in elements_index.items()}
        print(f"  events: {len(gameweeks)}, elements: {len(elements_index)}")
        _write_file(base_data_path, GAMEWEEKS_FILE_NAME, gameweeks)

        finished_gameweeks = [g["id"] for g in gameweeks if g.get("finished")]
        latest_finished_gw = finished_gameweeks[-1] if finished_gameweeks else None
        print(f"  latest finished gameweek: {latest_finished_gw}")

        cached_users = _read_file(base_data_path, USERS_FILE_NAME) or {}
        if cached_users:
            sample_user = next(iter(cached_users.values()))
            cached_latest_gw = (
                sample_user["history"][-1]["event"] if sample_user.get("history") else 0
            )
            print(f"  cached users latest gameweek: {cached_latest_gw}")

        users_globally_current = bool(cached_users) and not force_fetch_all and (
            latest_finished_gw is not None
            and all(
                _missing_gameweeks(cached_users.get(str(u["id"])), finished_gameweeks) == []
                for u in user_list
            )
        )

        encountered_error = False

        # 4. Per-user fetches — per-gameweek delta when possible.
        if not users_globally_current or force_fetch_all or fetch_live:
            print("\nFetching per-user data (per-gameweek delta)...")
            users_out: Dict[str, Any] = {} if force_fetch_all else dict(cached_users)
            for user_entry in user_list:
                uid = str(user_entry["id"])
                cached_user = None if force_fetch_all else users_out.get(uid)
                missing = _missing_gameweeks(cached_user, finished_gameweeks)
                if cached_user and not missing and not fetch_live:
                    # Truly nothing to fetch for this user; skip both the sleep and the calls.
                    print(f"  user: {user_entry['name']} (entry {uid}) — current, skipping")
                    continue

                print(f"\n  ({USER_SLEEP_SECONDS}s sleep to respect rate limit)")
                await asyncio.sleep(USER_SLEEP_SECONDS)
                print(f"  user: {user_entry['name']} (entry {uid})")

                try:
                    full_user = await _build_user_data(
                        api,
                        user_entry,
                        finished_gameweeks,
                        element_type_by_id,
                        cached_user=cached_user,
                    )
                    users_out[uid] = full_user
                except FPLApiError as e:
                    print(f"\n  !! API error for user {uid}: {e}")
                    encountered_error = True
                except Exception:
                    print(f"\n  !! Unexpected error for user {uid}:")
                    traceback.print_exception(*sys.exc_info())
                    encountered_error = True

            _write_file(base_data_path, USERS_FILE_NAME, users_out)
        else:
            print("\nUsers already up to date — skipping (use --force-fetch-all to refetch)")
            users_out = cached_users

        # 5. Players — only those picked by at least one user.
        cached_players = _read_file(base_data_path, PLAYERS_FILE_NAME) or {}
        players_out: Dict[str, Any] = {} if force_fetch_all else dict(cached_players)

        # Collect the set of player IDs touched by any pick across all users.
        touched_ids: set = set()
        for user in users_out.values():
            for gw_entry in user.get("history", []):
                for pick in gw_entry.get("picks", []):
                    touched_ids.add(int(pick["element"]))

        # Pick the set of player IDs we need fresh element-summary for.
        # A player's data is stale iff bootstrap-static.total_points differs
        # from what we cached — FPL updates `total_points` per gameweek as
        # data is checked, so it's a reliable freshness signal.
        candidate_ids = touched_ids | {int(pid) for pid in players_out.keys()}
        ids_to_fetch: List[int] = []
        skipped_current = 0
        for pid in sorted(candidate_ids):
            base = elements_index.get(pid)
            if base is None:
                continue
            if force_fetch_all:
                ids_to_fetch.append(pid)
                continue
            cached = players_out.get(str(pid))
            if cached is None or cached.get("total_points") != base.get("total_points"):
                ids_to_fetch.append(pid)
            else:
                # Refresh static fields in case other metadata changed,
                # but skip the (slow) element-summary call.
                players_out[str(pid)] = {**base, **{
                    k: cached.get(k, [])
                    for k in ("history", "fixtures", "history_past")
                }}
                skipped_current += 1

        print(
            f"\nPer-player fetch: {len(ids_to_fetch)} stale, "
            f"{skipped_current} current (skipped element-summary call)"
        )
        try:
            for i, player_id in enumerate(ids_to_fetch, start=1):
                base = elements_index[player_id]
                print(f"  ({i}/{len(ids_to_fetch)}) player {player_id} — {base.get('web_name')}")
                merged = await _merge_player_summary(api, base)
                players_out[str(player_id)] = merged
                await asyncio.sleep(PLAYER_SLEEP_SECONDS)
        except Exception:
            print("\n  !! Error fetching players:")
            traceback.print_exception(*sys.exc_info())
            encountered_error = True

        _write_file(base_data_path, PLAYERS_FILE_NAME, players_out)

        print()
        if encountered_error:
            print("Finished with errors.")
            sys.exit(2)
        else:
            print("Finished successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league", "-l", type=int, required=True, help="FPL classic league id")
    parser.add_argument(
        "--force-fetch-all",
        action="store_true",
        help="Re-fetch every user and player even if cached data looks current",
    )
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Include the current (unlocked) gameweek. Requires auth.",
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Use a fresh token from fpl_auth even for past data (rarely needed).",
    )
    args = parser.parse_args()

    asyncio.run(
        fetch_league_data(
            league_id=args.league,
            force_fetch_all=args.force_fetch_all,
            fetch_live=args.fetch_live,
            use_auth=args.auth,
        )
    )


if __name__ == "__main__":
    main()
