# Stats dashboard

Local Flask app that renders every `LeagueAnalyzer` stat as a card on a
single dark-mode page. Same content as `analyze_league.py` prints to the
terminal, but interactive: pick season + league from a dropdown, jump
between cards via a top-of-page TOC or a floating quick-jump menu.

## Running it

```bash
cd src && source env/bin/activate
pip install -r requirements-web.txt   # one-time
cd ..
bin/dev                               # starts Flask on :5000
```

Open <http://localhost:5000> .

That's it. The app reads from `src/data/<season>/<league_id>/` and auto-
discovers every season + league you've already fetched. No build step,
no extra processes.

### Behind a reverse proxy

If you want to serve the dashboard under a path prefix (e.g. so it
shares a hostname with other things on your machine), point any reverse
proxy at `localhost:5000` and have it forward `X-Forwarded-Prefix:
/<your-prefix>`. Flask's `ProxyFix` reads that into `SCRIPT_NAME` and
`url_for` emits the prefixed URLs automatically. Concrete Caddy example:

```caddy
handle_path /nplol/* {
    reverse_proxy localhost:5000 {
        header_up X-Forwarded-Prefix /nplol
    }
}
```

The reverse proxy is **not part of this repo** — it's a local choice,
not a project dependency. Direct hits on `:5000` always work without
any of this.

## What you see

- **Header** (sticky): season + league dropdowns, current GW indicator.
- **TOC** (Innhold): numbered grid of all stat titles, each an anchor link.
- **Cards**: one per stat. Title in gold serif (the Norwegian "ÅRETS X"),
  italic subtitle, a table of rows. The winner (row index 0) is highlighted
  gold with a 🏆 marker.
- **Floating ☰ button** (bottom-right): tap to open a tall scrollable list
  of every stat. Close via the `×`, an outside click, Escape, or by
  clicking any nav entry.

Inside cards:

- **Team-name cells** get a `P{rank}` place chip prefix derived from
  `analyzer.league.standings`, plus colored pill badges where applicable
  (e.g. YouTube / AI tags). Matching is substring-based, so it survives
  cross-season name variants like "Redlightning" vs "Red Lightning".
- **Paired GW stats** (highscore, lowscore, best/worst rank, most stable)
  show *which GW* the value occurred on as a small `GW{n}` badge tucked
  inline on the value cell. Backend supplies the mapping via
  `meta.sibling_gw_keys`.
- **Årets Visjonære** (GW1 picks): each row's squad is reconstructed from
  the analyzer's raw picks and rendered as a structured lineup
  GK → DEF → MID → FWD → Bench, with (C)/(VC) badges and the season-long
  "what-if" points per player.

## Architecture

```
Browser
   │
   ▼
Flask :5000  ── src/web/app.py
   │
   │  /api/seasons              enumerate src/data/<season>/<league_id>/
   │  /api/stats/<s>/<league>   instantiate LeagueAnalyzer, walk
   │                            STAT_SECTIONS, normalize rows, augment
   │                            squad/extremes/team-tags, return JSON
   │
   ▼
LeagueAnalyzer (in-process) ── reads src/data/<season>/<league>/*.json
```

### Files

```
src/web/
  app.py              Flask app + STAT_SECTIONS metadata + JSON serializer
  templates/
    index.html        Single-page dashboard (Tailwind via CDN)
  static/
    app.js            Vanilla JS renderer + TOC + jump menu
    style.css         Custom polish on top of Tailwind utilities
src/requirements-web.txt    Flask only
bin/dev                     One-line Flask launcher
```

### `STAT_SECTIONS` and the CLI drift point

`STAT_SECTIONS` in `app.py` lists the 38 stat cards with their Norwegian
"ÅRETS X" titles, Norwegian subtitles, and the `LeagueAnalyzer` method
to call. It duplicates the copy in `scripts/analyze_league.py` because
the CLI inlines its section labels into the print loop.

If you add a new public `get_*` method to `LeagueAnalyzer`, it needs an
entry in both places (CLI and `STAT_SECTIONS`). The snapshot test bench
will pick the method up automatically and verify the data, but the UI
title is manual. Re-lifting both into a shared constant is a future
cleanup; flagged in `app.py` and kept duplicated for now to avoid
touching the CLI flow.

### Row augmentation

Some analyzer methods return a structure that's awkward to render as a
flat row. The web layer post-processes a few of them in `_build_stats`,
keeping `LeagueAnalyzer` untouched:

| Method | What gets added |
|---|---|
| `get_gw1_picks_standings` | `squad`: position-sorted lineup parsed from picks + the analyzer's per-player season totals. Drops the flat `gw1_player_names` string. |
| `get_most_stable_user` | `highest_gw` and `lowest_gw`: which GW produced the user's best/worst score. |
| `get_highest_rank` | `highest_gw_rank_gw` and `highest_overall_rank_gw`: GWs for each best rank. |
| `get_lowest_rank` | `lowest_gw_rank_gw` and `lowest_overall_rank_gw`: GWs for each worst rank. |

All four pull from `analyzer.users[uid].history`, filtering out empty
GWs (`gameweek.highest_score == 0`) and unfinished GWs (`rank is None`),
matching the analyzer's own filtering in `get_least_gw_points` /
`get_most_gw_points`.

### Column ordering and hiding

`_columns_for` picks the visible columns from the first row, dropping
keys in `HIDDEN_KEYS` (internal IDs, sibling-GW pair keys, the flat
GW1 string, etc.) and complex list-of-dicts payloads. Then it sorts by
`COLUMN_PRIORITY` so the team name + GW context land first on narrow
mobile screens, with `squad` pushed to the right.

`COLUMN_LABELS` translates raw row keys to friendly headers. Anything
unmapped falls back to `key.replace("_", " ").title()`.

### Team tags

`_team_tags(analyzer)` returns `{user_id: {place, name, pills}}`. Place
comes straight from `analyzer.league.standings[*].rank`. Pills come from
substring matches in `TEAM_PILL_RULES` (lowercased). Adding a new pill =
add a row to `TEAM_PILL_RULES`, then add the color to `PILL_CLASS` in
`app.js` + a `.pill-<name>` style in `style.css`.

### Caching

Two in-process caches keyed by `(season, league_id)`:

- `_ANALYZER_CACHE`: a `LeagueAnalyzer` instance per league.
- `_STATS_CACHE`: the fully-rendered JSON payload per league.

Both auto-invalidate when `users.json`, `players.json`, `gameweeks.json`,
or `league.json` for that league has a newer mtime than the cached entry
(`_invalidate_if_stale`). Cost: one `stat()` per request, microseconds.

So the workflow after fetching new data is:

```bash
cd src && env/bin/python scripts/fetch_league.py --league=<id>
# refresh the dashboard in the browser — done. No restart.
```

### Static-asset cache busting

`index.html` appends `?v=<mtime>` to `app.js` and `style.css` URLs (see
`_inject_asset_version` in `app.py`). iOS Safari in particular caches
unversioned static URLs very aggressively; the query bust ensures a
normal refresh picks up new JS/CSS.

## Adding a new stat to the dashboard

1. Add a `get_*` method to `LeagueAnalyzer`. Make sure it accepts a
   `print_result` kwarg and returns a list of dict / Pydantic rows.
2. Add a row to `STAT_SECTIONS` in `src/web/app.py` with the Norwegian
   title, subtitle, and the method name. Order matters — it controls the
   visual order on the page.
3. If the analyzer omits useful context (like which GW something
   happened on), write an `_augment_<name>` helper and call it in
   `_build_stats`. Look at `_augment_stable` for a template.
4. If your method has columns that need a friendlier header, add an
   entry to `COLUMN_LABELS`. Default is title-cased snake_case.
5. If the method returns a tuple of multiple lists (like
   `get_best_differential`), add `"tuple_index": N` to the section dict
   and split into multiple `STAT_SECTIONS` entries.

The snapshot test bench picks up the new analyzer method automatically;
nothing to wire there.

## Known limitations

- **No live updates** — the page renders on load. If you fetch new data
  while the dashboard is open, refresh the browser. (The backend cache
  invalidates automatically, but the loaded page doesn't poll.)
- **In-progress gameweeks** — analyzer treats only `finished=True` GWs
  as data, mirroring the CLI behavior. So in-flight matches don't show
  up until FPL flips the flag.
- **Norwegian copy duplicated** between this dashboard and the CLI —
  see "STAT_SECTIONS and the CLI drift point" above.
