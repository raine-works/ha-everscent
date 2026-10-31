"""The EverScent integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EverScentApiError, EverScentAuth, EverScentAuthError, EverScentClient
from .const import CONF_REFRESH_TOKEN
from .coordinator import EverScentConfigEntry, EverScentDataUpdateCoordinator
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: EverScentConfigEntry
) -> bool:
    """Set up EverScent from a config entry."""
    session = async_get_clientsession(hass)
    auth = EverScentAuth(session, entry.data[CONF_REFRESH_TOKEN])
    time_zone = hass.config.time_zone or "UTC"
    client = EverScentClient(session, auth, time_zone)

    # Validate the stored token up front so a revoked token triggers reauth.
    try:
        await auth.async_get_id_token()
    except EverScentAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except EverScentApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = EverScentDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_setup_services(hass)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: EverScentConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
