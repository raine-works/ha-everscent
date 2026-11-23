"""Entity platform tests (require pytest-homeassistant-custom-component)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.const import (  # noqa: E402
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, State  # noqa: E402
from homeassistant.exceptions import HomeAssistantError  # noqa: E402
from homeassistant.helpers import (  # noqa: E402
    device_registry as dr,
    entity_registry as er,
)
from pytest_homeassistant_custom_component.common import (  # noqa: E402
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.everscent.api import (  # noqa: E402
    EverScentApiError,
    EverScentAuthError,
)
from custom_components.everscent.const import DOMAIN  # noqa: E402

DEVICE_ID = 1864
DURATION = "number.hallway_quick_scent_duration"


def _entity_id(hass: HomeAssistant, platform: str, key: str) -> str:
    """Look an entity up by its unique id, ``<device id>_<key>``."""
    entity_id = er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{DEVICE_ID}_{key}"
    )
    assert entity_id is not None
    return entity_id


def _state(hass: HomeAssistant, platform: str, key: str) -> State:
    state = hass.states.get(_entity_id(hass, platform, key))
    assert state is not None
    return state


async def _call(
    hass: HomeAssistant, domain: str, service: str, entity_id: str, **data: object
) -> None:
    await hass.services.async_call(
        domain, service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
    )


async def test_device_registered(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The diffuser becomes one device, named and identified from its detail."""
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, str(DEVICE_ID))})
    assert device is not None
    assert device.name == "Hallway"
    assert device.manufacturer == "EverScent"
    assert device.sw_version == "1.2.3"
    assert (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in device.connections


async def test_sensors(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    """Sensors read the device detail; diagnostic ones are disabled by default."""
    assert _state(hass, "sensor", "fragrance_level").state == "72"
    assert _state(hass, "sensor", "fragrance_name").state == "Linen"
    assert _state(hass, "sensor", "fragrance_category").state == "Fresh"
    assert _state(hass, "sensor", "concentration").state == "2"

    registry = er.async_get(hass)
    for key in ("firmware_version", "wifi_ssid", "location"):
        entry = registry.async_get(_entity_id(hass, "sensor", key))
        assert entry is not None
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_binary_sensors(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Binary sensors read the device detail flags."""
    assert _state(hass, "binary_sensor", "online").state == STATE_ON
    assert _state(hass, "binary_sensor", "fragrance_low").state == STATE_OFF
    assert _state(hass, "binary_sensor", "battery_low").state == STATE_ON
    assert _state(hass, "binary_sensor", "fan_active").state == STATE_ON
    assert _state(hass, "binary_sensor", "light_on").state == STATE_OFF


async def test_power_switch(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """The power switch shows isActive and sets power, then refreshes."""
    entity_id = _entity_id(hass, "switch", "power")
    assert hass.states.get(entity_id).state == STATE_ON

    mock_client.async_get_device.return_value["isActive"] = False
    await _call(hass, "switch", "turn_off", entity_id)
    mock_client.async_set_power.assert_awaited_with(DEVICE_ID, False)
    assert hass.states.get(entity_id).state == STATE_OFF

    await _call(hass, "switch", "turn_on", entity_id)
    mock_client.async_set_power.assert_awaited_with(DEVICE_ID, True)


async def test_schedule_switch(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Each schedule is a switch with its details, toggling it on the cloud."""
    entity_id = _entity_id(hass, "switch", "schedule_group-1")
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes["friendly_name"] == "Hallway Schedule 07:00-22:00"
    assert state.attributes["schedule_group_id"] == "group-1"
    assert state.attributes["days"] == [1, 2, 3]
    assert state.attributes["diffusing_seconds"] == 20
    assert state.attributes["pausing_seconds"] == 90
    assert state.attributes["concentration"] == 3

    await _call(hass, "switch", "turn_off", entity_id)
    mock_client.async_set_schedule_active.assert_awaited_with(
        DEVICE_ID, "group-1", False
    )
    await _call(hass, "switch", "turn_on", entity_id)
    mock_client.async_set_schedule_active.assert_awaited_with(
        DEVICE_ID, "group-1", True
    )


async def test_schedule_switch_unavailable_once_deleted(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A schedule that disappears from the cloud makes its switch unavailable."""
    entity_id = _entity_id(hass, "switch", "schedule_group-1")
    mock_client.async_get_schedules.return_value = []
    await init_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


@pytest.mark.parametrize(
    ("error", "translation_key"),
    [
        (EverScentApiError("boom"), "api_error"),
        (EverScentAuthError("revoked"), "auth_failed"),
    ],
)
async def test_failed_action_raises_home_assistant_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: AsyncMock,
    error: Exception,
    translation_key: str,
) -> None:
    """A client error in a user action surfaces as a translated HomeAssistantError."""
    mock_client.async_set_power.side_effect = error
    with pytest.raises(HomeAssistantError) as exc_info:
        await _call(hass, "switch", "turn_on", _entity_id(hass, "switch", "power"))
    assert exc_info.value.translation_domain == DOMAIN
    assert exc_info.value.translation_key == translation_key


async def test_quick_scent_uses_duration_number(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """The quick-scent button sends the duration the number entity holds."""
    button = _entity_id(hass, "button", "quick_scent")
    number = _entity_id(hass, "number", "quick_scent_duration")
    assert hass.states.get(number).state == "30"

    await _call(hass, "button", "press", button)
    mock_client.async_quick_scent.assert_awaited_with(DEVICE_ID, 30)

    await _call(hass, "number", "set_value", number, value=12)
    assert hass.states.get(number).state == "12"
    await _call(hass, "button", "press", button)
    mock_client.async_quick_scent.assert_awaited_with(DEVICE_ID, 12)


async def test_quick_scent_duration_restored(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    config_entry: MockConfigEntry,
    mock_client: AsyncMock,
) -> None:
    """The duration survives a restart, clamped to the allowed range."""
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(DURATION, "500"),
                {
                    "native_value": 500,
                    "native_min_value": 5,
                    "native_max_value": 120,
                    "native_step": 1,
                    "native_unit_of_measurement": "s",
                },
            )
        ],
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(DURATION).state == "120"


async def test_acknowledge_bottle_button(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """The disabled-by-default acknowledge button, once enabled, calls the API."""
    registry = er.async_get(hass)
    entity_id = _entity_id(hass, "button", "ack_empty_bottle")
    assert hass.states.get(entity_id) is None

    registry.async_update_entity(entity_id, disabled_by=None)
    assert await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()

    await _call(hass, "button", "press", entity_id)
    mock_client.async_acknowledge_empty_bottle.assert_awaited_once_with(DEVICE_ID)
