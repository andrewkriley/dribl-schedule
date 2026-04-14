"""Config flow — guided wizard so the user only needs to know their team name."""
from __future__ import annotations

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DriblApi, DriblApiError
from .const import DOMAIN


class DriblConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._api: DriblApi | None = None
        self._tenant: dict = {}
        self._clubs: list[dict] = []
        self._seasons: list[dict] = []
        self._competitions: list[dict] = []
        self._leagues: list[dict] = []
        self._club_id: str = ""
        self._club_name: str = ""
        self._season_id: str = ""
        self._season_name: str = ""
        self._competition_id: str = ""
        self._competition_name: str = ""

    # ------------------------------------------------------------------ #
    # Step 1 — Association slug                                            #
    # ------------------------------------------------------------------ #
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            slug = user_input["association_slug"].strip().lower()
            # Accept full URLs like "nwsf.dribl.com" or just "nwsf"
            if ".dribl.com" in slug:
                slug = slug.split(".dribl.com")[0].split("//")[-1]

            session = async_get_clientsession(self.hass)
            self._api = DriblApi(session)

            try:
                self._tenant = await self._api.resolve_tenant(slug)
                self._clubs = await self._api.get_clubs(self._tenant["id"])
                self._seasons = await self._api.get_seasons(self._tenant["id"])
            except DriblApiError as e:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_club()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("association_slug"): str,
            }),
            description_placeholders={
                "example": "nwsf  (from nwsf.dribl.com)"
            },
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Step 2 — Club                                                        #
    # ------------------------------------------------------------------ #
    async def async_step_club(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._club_id = user_input["club"]
            self._club_name = next(
                c["name"] for c in self._clubs if c["id"] == self._club_id
            )
            self._season_id = self._seasons[0]["id"]
            self._season_name = self._seasons[0]["name"]

            try:
                self._competitions = await self._api.get_competitions(
                    self._tenant["id"], self._season_id
                )
            except DriblApiError:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_competition()

        club_options = {c["id"]: c["name"] for c in self._clubs}
        return self.async_show_form(
            step_id="club",
            data_schema=vol.Schema({
                vol.Required("club"): vol.In(club_options),
            }),
            description_placeholders={"association": self._tenant["name"]},
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Step 3 — Competition                                                 #
    # ------------------------------------------------------------------ #
    async def async_step_competition(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._competition_id = user_input["competition"]
            self._competition_name = next(
                c["name"] for c in self._competitions if c["id"] == self._competition_id
            )
            try:
                self._leagues = await self._api.get_leagues(
                    self._tenant["id"], self._competition_id, self._club_id
                )
            except DriblApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self._leagues:
                    errors["base"] = "no_leagues"
                else:
                    return await self.async_step_league()

        comp_options = {c["id"]: c["name"] for c in self._competitions}
        return self.async_show_form(
            step_id="competition",
            data_schema=vol.Schema({
                vol.Required("competition"): vol.In(comp_options),
            }),
            description_placeholders={"club": self._club_name},
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # Step 4 — League (team)                                               #
    # ------------------------------------------------------------------ #
    async def async_step_league(self, user_input=None):
        if user_input is not None:
            league_id = user_input["league"]
            league_name = next(
                l["name"] for l in self._leagues if l["id"] == league_id
            )
            title = f"{self._club_name} — {league_name}"

            await self.async_set_unique_id(f"{self._tenant['id']}_{self._club_id}_{league_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=title,
                data={
                    "tenant_id": self._tenant["id"],
                    "tenant_name": self._tenant["name"],
                    "tenant_slug": self._tenant["slug"],
                    "club_id": self._club_id,
                    "club_name": self._club_name,
                    "season_id": self._season_id,
                    "season_name": self._season_name,
                    "competition_id": self._competition_id,
                    "competition_name": self._competition_name,
                    "league_id": league_id,
                    "league_name": league_name,
                },
            )

        league_options = {l["id"]: l["name"] for l in self._leagues}
        return self.async_show_form(
            step_id="league",
            data_schema=vol.Schema({
                vol.Required("league"): vol.In(league_options),
            }),
            description_placeholders={
                "club": self._club_name,
                "competition": self._competition_name,
            },
        )
