"""DataUpdateCoordinator — polls Dribl API on a schedule."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DriblApi, DriblApiError
from .const import DOMAIN, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class DriblCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        self._api = DriblApi(async_get_clientsession(hass))
        self._entry_data = entry_data

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> list[dict]:
        d = self._entry_data
        try:
            return await self._api.get_fixtures(
                tenant_id=d["tenant_id"],
                season_id=d["season_id"],
                competition_id=d["competition_id"],
                club_id=d["club_id"],
                league_id=d["league_id"],
            )
        except DriblApiError as e:
            raise UpdateFailed(str(e)) from e
