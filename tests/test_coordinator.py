"""Setup and polling tests (require pytest-homeassistant-custom-component)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState  # noqa: E402
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.util import dt as dt_util  # noqa: E402
from pytest_homeassistant_custom_component.common import (  # noqa: E402
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.everscent.api import (  # noqa: E402
    EverScentApiError,
    EverScentAuthError,
)
from custom_components.everscent.const import (  # noqa: E402
    CONF_REFRESH_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

POWER = "switch.hallway_power"


async def _poll(hass: HomeAssistant) -> None:
    """Advance time past the scan interval so the coordinator polls."""
    async_fire_time_changed(
        hass, dt_util.utcnow() + DEFAULT_SCAN_INTERVAL + timedelta(seconds=1)
    )
    await hass.async_block_till_done()


def _reauth_flows(hass: HomeAssistant) -> list[dict]:
    return [
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["handler"] == DOMAIN and flow["context"]["source"] == SOURCE_REAUTH
    ]


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """An entry with a valid token loads, polls once, and unloads cleanly."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(POWER).state == STATE_ON

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    ("error", "state"),
    [
        (EverScentAuthError("TOKEN_EXPIRED"), ConfigEntryState.SETUP_ERROR),
        (EverScentApiError("down"), ConfigEntryState.SETUP_RETRY),
    ],
)
async def test_setup_token_errors(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    config_entry: MockConfigEntry,
    mock_client: AsyncMock,
    error: Exception,
    state: ConfigEntryState,
) -> None:
    """A rejected token fails setup into reauth; other errors retry setup."""
    config_entry.add_to_hass(hass)
    with patch("custom_components.everscent.EverScentAuth") as auth:
        auth.return_value.async_get_id_token = AsyncMock(side_effect=error)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is state
    assert bool(_reauth_flows(hass)) is isinstance(error, EverScentAuthError)


async def test_poll_api_error_marks_entities_unavailable(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A failed poll (UpdateFailed) makes entities unavailable until it recovers."""
    mock_client.async_get_device_list.side_effect = EverScentApiError("down")
    await _poll(hass)
    assert hass.states.get(POWER).state == STATE_UNAVAILABLE
    assert not _reauth_flows(hass)

    mock_client.async_get_device_list.side_effect = None
    await _poll(hass)
    assert hass.states.get(POWER).state == STATE_ON


async def test_poll_auth_error_starts_reauth(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A token rejected during a poll starts a reauth flow."""
    mock_client.async_get_schedules.side_effect = EverScentAuthError("revoked")
    await _poll(hass)

    assert hass.states.get(POWER).state == STATE_UNAVAILABLE
    flows = _reauth_flows(hass)
    assert len(flows) == 1
    assert flows[0]["context"]["entry_id"] == init_integration.entry_id


async def test_rotated_refresh_token_is_saved(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """When Firebase rotates the refresh token, the entry stores the new one."""
    assert init_integration.data[CONF_REFRESH_TOKEN] == "refresh"

    mock_client.auth.refresh_token = "rotated"
    await _poll(hass)

    assert init_integration.data[CONF_REFRESH_TOKEN] == "rotated"
    assert init_integration.data["email"] == "user@example.com"


async def test_unchanged_refresh_token_does_not_update_entry(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A poll that keeps the same token leaves the entry alone."""
    with patch.object(hass.config_entries, "async_update_entry") as update:
        await _poll(hass)
    update.assert_not_called()
