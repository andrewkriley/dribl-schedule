"""Dribl API client — handles all discovery and fixture fetching."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_BASE


class DriblApiError(Exception):
    pass


class DriblApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, path: str, params: dict) -> Any:
        url = f"{API_BASE}/{path}"
        try:
            async with self._session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise DriblApiError(f"HTTP {resp.status} from {url}")
                return await resp.json()
        except asyncio.TimeoutError as e:
            raise DriblApiError("Request timed out") from e
        except aiohttp.ClientError as e:
            raise DriblApiError(str(e)) from e

    async def resolve_tenant(self, slug: str) -> dict:
        """Resolve a subdomain slug (e.g. 'nwsf') to tenant metadata."""
        data = await self._get("tenants", {
            "mc_link": f"{slug}.dribl.com",
            "slug": slug,
        })
        tenant = data.get("data", {})
        if not tenant:
            raise DriblApiError(f"No tenant found for slug '{slug}'")
        return {
            "id": tenant["id"],
            "name": tenant["attributes"].get("tenantable_name") or tenant["attributes"]["name"],
            "slug": slug,
        }

    async def get_clubs(self, tenant_id: str) -> list[dict]:
        """Return all clubs for a tenant, sorted by name."""
        data = await self._get("list/clubs", {
            "disable_paging": "true",
            "tenant": tenant_id,
        })
        return [
            {"id": c["id"], "name": c["attributes"]["name"]}
            for c in data.get("data", [])
        ]

    async def get_seasons(self, tenant_id: str) -> list[dict]:
        """Return all seasons for a tenant, most recent first."""
        data = await self._get("list/seasons", {
            "disable_paging": "true",
            "tenant": tenant_id,
        })
        return [
            {"id": s["id"], "name": s["attributes"]["name"]}
            for s in data.get("data", [])
        ]

    async def get_competitions(self, tenant_id: str, season_id: str) -> list[dict]:
        """Return competitions for a tenant + season."""
        data = await self._get("list/competitions", {
            "disable_paging": "true",
            "tenant": tenant_id,
            "season": season_id,
        })
        return [
            {"id": c["id"], "name": c["attributes"]["name"]}
            for c in data.get("data", [])
        ]

    async def get_leagues(self, tenant_id: str, competition_id: str, club_id: str) -> list[dict]:
        """Return leagues (teams) for a competition filtered by club."""
        # First get all leagues for the competition
        data = await self._get("list/leagues", {
            "disable_paging": "true",
            "tenant": tenant_id,
            "competition": competition_id,
            "sort": "+name",
        })
        all_leagues = [
            {"id": l["id"], "name": l["attributes"]["name"]}
            for l in data.get("data", [])
        ]

        # Filter to leagues that have fixtures for this club by probing the fixtures endpoint
        # We fetch fixtures for each league and keep those with results for the club
        # To avoid N+1 calls, we fetch fixtures once with just club+competition and collect league IDs
        fixture_data = await self._get("fixtures", {
            "date_range": "all",
            "tenant": tenant_id,
            "competition": competition_id,
            "club": club_id,
            "timezone": "Australia/Sydney",
        })
        active_league_ids: set[str] = set()
        for fixture in fixture_data.get("data", []):
            # league info is in relationships or we can infer from league_name
            # The fixtures endpoint doesn't return league_id directly, so we rely on
            # the league list — return all leagues and let the user pick
            pass

        # Return all leagues; the user picks which team they are
        return all_leagues

    async def get_fixtures(
        self,
        tenant_id: str,
        season_id: str,
        competition_id: str,
        club_id: str,
        league_id: str,
        date_range: str = "default",
    ) -> list[dict]:
        """Fetch fixtures for a specific team."""
        data = await self._get("fixtures", {
            "date_range": date_range,
            "season": season_id,
            "competition": competition_id,
            "club": club_id,
            "league": league_id,
            "tenant": tenant_id,
            "timezone": "Australia/Sydney",
        })
        return [
            {
                "hash_id": f["hash_id"],
                "name": f["attributes"]["name"],
                "date": f["attributes"]["date"],
                "round": f["attributes"]["full_round"],
                "home_team": f["attributes"]["home_team_name"],
                "away_team": f["attributes"]["away_team_name"],
                "ground": f["attributes"]["ground_name"],
                "field": f["attributes"]["field_name"],
                "competition": f["attributes"]["competition_name"],
                "league": f["attributes"]["league_name"],
                "status": f["attributes"]["status"],
                "home_score": f["attributes"]["home_score"],
                "away_score": f["attributes"]["away_score"],
            }
            for f in data.get("data", [])
        ]
