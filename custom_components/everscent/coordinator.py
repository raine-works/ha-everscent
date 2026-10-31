"""Data update coordinator for EverScent."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EverScentApiError, EverScentAuthError, EverScentClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type EverScentConfigEntry = ConfigEntry[EverScentDataUpdateCoordinator]


class EverScentDataUpdateCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Polls the EverScent cloud and keeps per-device state in memory.

    ``data`` maps device_id -> {"detail": {...}, "schedules": [...]}.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EverScentConfigEntry,
        client: EverScentClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client
        self._last_refresh_token = client.auth.refresh_token
        # Per-device quick-scent duration (seconds), owned by the number entity.
        self.quick_scent_durations: dict[int, int] = {}

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch the device list and each device's detail + schedules."""
        try:
            devices = await self.client.async_get_device_list()
            result: dict[int, dict[str, Any]] = {}
            for dev in devices:
                device_id = dev["id"]
                detail = await self.client.async_get_device(device_id)
                schedules = await self.client.async_get_schedules(device_id)
                result[device_id] = {"detail": detail, "schedules": schedules}
        except EverScentAuthError as err:
            # Surface as reauth-triggering error.
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except EverScentApiError as err:
            raise UpdateFailed(f"Error communicating with EverScent: {err}") from err

        self._persist_rotated_token()
        return result

    def _persist_rotated_token(self) -> None:
        """If Firebase rotated the refresh token, write it back to the entry."""
        current = self.client.auth.refresh_token
        if current == self._last_refresh_token or self.config_entry is None:
            return
        self._last_refresh_token = current
        new_data = {**self.config_entry.data, "refresh_token": current}
        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
