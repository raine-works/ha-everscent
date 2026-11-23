"""Action tests (require pytest-homeassistant-custom-component)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import ConfigEntryState  # noqa: E402
from homeassistant.const import EVENT_SERVICE_REGISTERED  # noqa: E402
from homeassistant.core import Event, HomeAssistant  # noqa: E402
from homeassistant.exceptions import (  # noqa: E402
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.setup import async_setup_component  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.everscent.api import EverScentApiError  # noqa: E402
from custom_components.everscent.const import (  # noqa: E402
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

CLIENT = "custom_components.everscent.EverScentClient"
AUTH = "custom_components.everscent.EverScentAuth"
DELETE = {"schedule_group_id": "group-1"}


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations: None) -> None:
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


SCHEDULE = {
    "device_id": 1864,
    "days": [1, 2],
    "start_time": "07:00",
    "end_time": "22:00",
}
CUSTOM = {"diffusing_seconds": 20, "pausing_seconds": 90, "concentration": 3}


async def test_set_schedule_creates_custom_schedule(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Without a group id, set_schedule creates a schedule with custom values."""
    await hass.services.async_call(
        DOMAIN, "set_schedule", {**SCHEDULE, **CUSTOM}, blocking=True
    )
    mock_client.async_create_schedule.assert_awaited_once_with(
        {
            "deviceId": 1864,
            "days": [1, 2],
            "startTime": "07:00",
            "endTime": "22:00",
            "isActive": True,
            "isStandardSetting": False,
            "customSetting": {"diffusing": 20, "pausing": 90, "concentration": 3},
        }
    )
    mock_client.async_update_schedule.assert_not_awaited()


async def test_set_schedule_updates_with_standard_setting(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """With a group id, set_schedule updates that schedule."""
    await hass.services.async_call(
        DOMAIN,
        "set_schedule",
        {**SCHEDULE, "schedule_group_id": "group-1", "standard_setting_id": 3},
        blocking=True,
    )
    mock_client.async_update_schedule.assert_awaited_once_with(
        {
            "deviceId": 1864,
            "days": [1, 2],
            "startTime": "07:00",
            "endTime": "22:00",
            "isActive": True,
            "isStandardSetting": True,
            "standardSettingId": 3,
            "scheduleGroupId": "group-1",
        }
    )
    mock_client.async_create_schedule.assert_not_awaited()


@pytest.mark.parametrize(
    ("data", "match"),
    [
        ({**SCHEDULE, "diffusing_seconds": 20}, "standard_setting_id"),
        ({**SCHEDULE, "device_id": 999, "standard_setting_id": 3}, "Unknown"),
    ],
)
async def test_set_schedule_rejects_bad_input(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: AsyncMock,
    data: dict[str, Any],
    match: str,
) -> None:
    """Partial custom settings or an unknown device are refused, sending nothing."""
    with pytest.raises(ServiceValidationError, match=match):
        await hass.services.async_call(DOMAIN, "set_schedule", data, blocking=True)
    mock_client.async_create_schedule.assert_not_awaited()
    mock_client.async_update_schedule.assert_not_awaited()


async def test_delete_schedule(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """delete_schedule deletes the schedule by group id."""
    await hass.services.async_call(DOMAIN, "delete_schedule", DELETE, blocking=True)
    mock_client.async_delete_schedule.assert_awaited_once_with("group-1")


async def test_action_api_error_raises_home_assistant_error(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A client error during an action surfaces as HomeAssistantError."""
    mock_client.async_delete_schedule.side_effect = EverScentApiError("boom")
    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(DOMAIN, "delete_schedule", DELETE, blocking=True)
    assert exc_info.value.translation_key == "api_error"
