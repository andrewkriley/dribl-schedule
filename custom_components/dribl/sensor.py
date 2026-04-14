"""Sensor platform — one sensor per configured team."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DriblCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DriblCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DriblFixtureSensor(coordinator, entry)])


class DriblFixtureSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:soccer"

    def __init__(self, coordinator: DriblCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.title

    @property
    def native_value(self) -> str | None:
        """State is the next fixture datetime as an ISO string, or 'No upcoming fixtures'."""
        fixture = self._next_fixture()
        if fixture is None:
            return "No upcoming fixtures"
        return fixture["date"]

    @property
    def extra_state_attributes(self) -> dict:
        fixture = self._next_fixture()
        if fixture is None:
            return {"all_fixtures": self.coordinator.data or []}

        return {
            "round": fixture["round"],
            "home_team": fixture["home_team"],
            "away_team": fixture["away_team"],
            "ground": fixture["ground"],
            "field": fixture["field"],
            "competition": fixture["competition"],
            "league": fixture["league"],
            "status": fixture["status"],
            "home_score": fixture["home_score"],
            "away_score": fixture["away_score"],
            "all_fixtures": self.coordinator.data or [],
            # Config metadata
            "club": self._entry.data["club_name"],
            "association": self._entry.data["tenant_name"],
            "season": self._entry.data["season_name"],
        }

    def _next_fixture(self) -> dict | None:
        fixtures = self.coordinator.data
        if not fixtures:
            return None
        now = datetime.now(tz=timezone.utc)
        upcoming = [
            f
            for f in fixtures
            if f["status"] == "pending"
            and datetime.fromisoformat(f["date"].replace("Z", "+00:00")) > now
        ]
        return upcoming[0] if upcoming else None
