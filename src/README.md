# FPL Mini League Statistics

Get fun and mind-blowing statistics about your FPL mini league season.

Shout out to `https://github.com/amosbastian/fpl` for making my life easier.

## Setup / installation

Install pyenv
```
brew install pyenv
```

Install and enable Python v13
```
pyenv install 3.13
pyenv global 3.13
```

Create virtual env

```
virtualenv env
```

Activate virtual env

```
source env/bin/activate
```

Install requirements

```
pip install -r requirements.txt
```

## Headless auth (optional)

`fetch_league.py` hits the FPL public API directly and works without any credentials for past/finished gameweeks. You only need auth for the in-flight gameweek before it locks. See [`docs/HEADLESS-AUTH.md`](../docs/HEADLESS-AUTH.md) for the one-time Playwright + `~/.fpl/credentials.env` setup if/when you need `--fetch-live`.

## Fetch league data

Before analyzing, you need to fetch data. To fetch data for your league up to the latest finished gameweek, run:

```
python scripts/fetch_league.py \
    --league=<fpl_league_id> \
    [--force-fetch-all] \
    [--fetch-live] \
    [--auth]
```

No email/cookie needed — past gameweeks are public.

- `--force-fetch-all` ignores the cache and re-fetches every user and player.
- `--fetch-live` includes the current (still unlocked) gameweek. Requires a token from `python scripts/refresh_token.py` first.
- `--auth` attaches a fresh token even for past data. Rarely needed.

This will fetch data from `fantasy.premierleague.com` and output the following files:

- `data/<season>/<league_id>/league.json` # league info up to the latest gameweek
- `data/<season>/<league_id>/gameweeks.json` # gameweeks up to the latest gameweek
- `data/<season>/<league_id>/user_list.json` # simple list of users in league, with id and name
- `data/<season>/<league_id>/users.json` # complete set of user data ut to the latest gameweek, including gameweek history, picks, auto-subs and chip usage
- `data/<season>/<league_id>/players.json` # player info for all players selected by at least one of the users in the mini league in at least one gameweek, up to the latest gameweek
  These are more or less the raw json responses returned from `fantasy.premierleague.com` dumped to file

## Analyze league data

After fecthing data you can analyze your mini league season data by running:

```
python fpl-stats/scripts/analyze_league.py \
    --season=<startyear_endyear> \
    --league=<fpl_league_id> \
    [--live] \
    [--disable-prompt] \
    [> <output_file>]
```

This will output all statistics for your league.  
If you want to analyze the current/ongoing gameweek "live", add the `--live` argument flag.  
If you don't want to press Enter to continue between each statistic, add the `--disable-prompt` argument.  
You could also output the results to file by adding `> output.txt` if you want to store the results.

You could also start your own python shell and get the statistics you are interested in, e.g.

```
python
>>> from fplstats.analyzers import LeagueAnalyzer
>>> # Init
>>> league_analyzer = LeagueAnalyzer(<season_id>, <league_id>)
>>> # Get the statistics you want, e.g.
>>> league_analyzer.get_captain_hindsight()
TEAM          CAPTAIN POINTS
Soccer MC's   1413
CHANGE NAME   1337
>>> # Etc.
```
