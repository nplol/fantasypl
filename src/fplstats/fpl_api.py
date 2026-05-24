"""
Async FPL API client.

Talks to fantasy.premierleague.com/api directly using aiohttp, with optional
token auth from `fpl_auth.get_valid_token()`. Most endpoints used by
fetch_league.py are public and work without a token; the token is only
required for live/in-flight picks before a gameweek locks.

This replaces the legacy `fpl` Python library which has been unreliable
since FPL migrated to OAuth2 PKCE auth.

USAGE:

    from fplstats.fpl_api import FPLApiClient

    async with FPLApiClient() as api:
        bootstrap = await api.get_bootstrap_static()
        standings = await api.get_classic_league_standings(1026627)
        picks = await api.get_entry_picks(entry_id=3620812, gameweek=1)
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import aiohttp

BASE_URL = "https://fantasy.premierleague.com/api"

USER_AGENT = (
    "FPL-NPLOL-Stats/1.0 "
    "(+https://github.com/nplol/fantasypl)"
)


class FPLApiError(Exception):
    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


class FPLApiClient:
    """
    Minimal async wrapper for the FPL public API.

    Pass `token` (with or without "Bearer " prefix) to authenticate calls
    that need it. All token-less calls still work for public data.
    """

    def __init__(self, token: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self._token = token
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "FPLApiClient":
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Origin": "https://fantasy.premierleague.com",
            "Referer": "https://fantasy.premierleague.com/",
            "x-requested-with": "XMLHttpRequest",
            "Accept": "application/json",
        }
        if self._token:
            tok = self._token if self._token.startswith("Bearer ") else f"Bearer {self._token}"
            # FPL accepts either header; X-Api-Authorization is what the SPA sends.
            headers["X-Api-Authorization"] = tok
        return headers

    async def _get(self, path: str, retries: int = 2) -> Any:
        assert self._session is not None, "Use FPLApiClient as an async context manager"
        url = f"{BASE_URL}/{path.lstrip('/')}"
        backoff = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                async with self._session.get(url, headers=self._headers()) as resp:
                    if resp.status == 429:
                        # Rate limited — exponential backoff and retry.
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    if resp.status >= 400:
                        text = await resp.text()
                        raise FPLApiError(
                            f"GET {url} -> {resp.status}: {text[:200]}",
                            status=resp.status,
                        )
                    return await resp.json()
            except aiohttp.ClientError as e:
                last_exc = e
                if attempt < retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        if last_exc:
            raise last_exc
        raise FPLApiError(f"GET {url} -> exhausted retries", status=0)

    # --- Bootstrap / static catalog --------------------------------------

    async def get_bootstrap_static(self) -> Dict[str, Any]:
        """Returns events, teams, elements (players), element_types, etc."""
        return await self._get("bootstrap-static/")

    # --- League ----------------------------------------------------------

    async def get_classic_league_standings(self, league_id: int, page: int = 1) -> Dict[str, Any]:
        """
        Returns league info (`league`) + paginated standings (`standings`).
        For NPLOL's 10-user league, one page is enough.
        """
        return await self._get(f"leagues-classic/{league_id}/standings/?page_standings={page}")

    # --- Per-entry (manager) ---------------------------------------------

    async def get_entry(self, entry_id: int) -> Dict[str, Any]:
        """Manager metadata."""
        return await self._get(f"entry/{entry_id}/")

    async def get_entry_history(self, entry_id: int) -> Dict[str, Any]:
        """Returns `current` (per-gameweek history), `past`, `chips`."""
        return await self._get(f"entry/{entry_id}/history/")

    async def get_entry_picks(self, entry_id: int, gameweek: int) -> Dict[str, Any]:
        """Returns `picks`, `automatic_subs`, `entry_history`, `active_chip`."""
        return await self._get(f"entry/{entry_id}/event/{gameweek}/picks/")

    async def get_entry_transfers(self, entry_id: int) -> List[Dict[str, Any]]:
        """All transfers across all gameweeks (excluding free transfers within wildcard/free-hit)."""
        return await self._get(f"entry/{entry_id}/transfers/")

    # --- Per-player ------------------------------------------------------

    async def get_element_summary(self, element_id: int) -> Dict[str, Any]:
        """Returns `history` (per-GW), `history_past` (prev seasons), `fixtures` (upcoming)."""
        return await self._get(f"element-summary/{element_id}/")

    # --- /api/me/ (auth check) -------------------------------------------

    async def get_me(self) -> Dict[str, Any]:
        """Requires auth. Returns the manager attached to the token."""
        return await self._get("me/")
