"""Action registration tests (require pytest-homeassistant-custom-component)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import ConfigEntryState  # noqa: E402
from homeassistant.const import EVENT_SERVICE_REGISTERED  # noqa: E402
from homeassistant.core import Event, HomeAssistant  # noqa: E402
from homeassistant.exceptions import ServiceValidationError  # noqa: E402
from homeassistant.setup import async_setup_component  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.everscent.const import (  # noqa: E402
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

CLIENT = "custom_components.everscent.EverScentClient"
AUTH = "custom_components.everscent.EverScentAuth"
DELETE = {"schedule_group_id": "group-1"}


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the custom integration during tests."""
    return


def _entry(email: str) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=email,
        data={"email": email, CONF_REFRESH_TOKEN: "refresh"},
    )


async def test_actions_exist_without_an_entry(hass: HomeAssistant) -> None:
    """Actions are registered when the integration loads, not per entry."""
    assert await async_setup_component(hass, DOMAIN, {})

    assert hass.services.has_service(DOMAIN, "set_schedule")
    assert hass.services.has_service(DOMAIN, "delete_schedule")
    with pytest.raises(ServiceValidationError, match="No EverScent account"):
        await hass.services.async_call(DOMAIN, "delete_schedule", DELETE, blocking=True)


async def test_actions_registered_once_and_kept_across_entries(
    hass: HomeAssistant,
) -> None:
    """Two entries share one registration, and unloading them removes nothing."""
    entries = [_entry("a@example.com"), _entry("b@example.com")]
    client = AsyncMock()
    client.async_get_device_list.return_value = []
    with (
        patch(CLIENT, return_value=client),
        patch(AUTH) as auth,
    ):
        registered: list[tuple[str, str]] = []

        def _on_registered(event: Event) -> None:
            if event.data["domain"] == DOMAIN:
                registered.append((DOMAIN, event.data["service"]))

        hass.bus.async_listen(EVENT_SERVICE_REGISTERED, _on_registered)
        auth.return_value.async_get_id_token = AsyncMock()
        for entry in entries:
            entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entries[0].entry_id)
        await hass.async_block_till_done()
        assert [e.state for e in entries] == [ConfigEntryState.LOADED] * 2

        assert sorted(registered) == [
            (DOMAIN, "delete_schedule"),
            (DOMAIN, "set_schedule"),
        ]

        for entry in entries:
            assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, "set_schedule")
    assert hass.services.has_service(DOMAIN, "delete_schedule")
