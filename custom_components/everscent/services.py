"""Services for EverScent (schedule management)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import EverScentDataUpdateCoordinator

SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"

ATTR_DEVICE_ID = "device_id"
ATTR_SCHEDULE_GROUP_ID = "schedule_group_id"
ATTR_DAYS = "days"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_STANDARD_SETTING_ID = "standard_setting_id"
ATTR_DIFFUSING = "diffusing_seconds"
ATTR_PAUSING = "pausing_seconds"
ATTR_CONCENTRATION = "concentration"

SET_SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): vol.Coerce(int),
        vol.Optional(ATTR_SCHEDULE_GROUP_ID): cv.string,
        vol.Required(ATTR_DAYS): vol.All(
            cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))]
        ),
        vol.Required(ATTR_START_TIME): cv.string,
        vol.Required(ATTR_END_TIME): cv.string,
        vol.Optional(ATTR_STANDARD_SETTING_ID): vol.Coerce(int),
        vol.Optional(ATTR_DIFFUSING): vol.Coerce(int),
        vol.Optional(ATTR_PAUSING): vol.Coerce(int),
        vol.Optional(ATTR_CONCENTRATION): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=3)
        ),
    }
)

DELETE_SCHEDULE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SCHEDULE_GROUP_ID): cv.string}
)


def _find_coordinator(
    hass: HomeAssistant, device_id: int | None = None
) -> EverScentDataUpdateCoordinator:
    """Return the coordinator owning ``device_id`` (or the only one)."""
    coordinators: list[EverScentDataUpdateCoordinator] = [
        entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state.recoverable and getattr(entry, "runtime_data", None)
    ]
    if not coordinators:
        raise ServiceValidationError("No EverScent account is configured")
    if device_id is not None:
        for coordinator in coordinators:
            if device_id in coordinator.data:
                return coordinator
        raise ServiceValidationError(f"Unknown EverScent device id {device_id}")
    return coordinators[0]


async def _handle_set_schedule(call: ServiceCall) -> None:
    """Create or update a schedule."""
    data = call.data
    device_id = data[ATTR_DEVICE_ID]
    coordinator = _find_coordinator(call.hass, device_id)

    payload: dict[str, Any] = {
        "deviceId": device_id,
        "days": data[ATTR_DAYS],
        "startTime": data[ATTR_START_TIME],
        "endTime": data[ATTR_END_TIME],
        "isActive": True,
    }

    if ATTR_STANDARD_SETTING_ID in data:
        payload["isStandardSetting"] = True
        payload["standardSettingId"] = data[ATTR_STANDARD_SETTING_ID]
    elif all(k in data for k in (ATTR_DIFFUSING, ATTR_PAUSING, ATTR_CONCENTRATION)):
        payload["isStandardSetting"] = False
        payload["customSetting"] = {
            "diffusing": data[ATTR_DIFFUSING],
            "pausing": data[ATTR_PAUSING],
            "concentration": data[ATTR_CONCENTRATION],
        }
    else:
        raise ServiceValidationError(
            "Provide either standard_setting_id, or all of diffusing_seconds, "
            "pausing_seconds and concentration"
        )

    if ATTR_SCHEDULE_GROUP_ID in data:
        payload["scheduleGroupId"] = data[ATTR_SCHEDULE_GROUP_ID]
        await coordinator.client.async_update_schedule(payload)
    else:
        await coordinator.client.async_create_schedule(payload)

    await coordinator.async_request_refresh()


async def _handle_delete_schedule(call: ServiceCall) -> None:
    """Delete a schedule by its group id."""
    coordinator = _find_coordinator(call.hass)
    await coordinator.client.async_delete_schedule(
        call.data[ATTR_SCHEDULE_GROUP_ID]
    )
    await coordinator.async_request_refresh()


def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_SCHEDULE):
        return
    hass.services.async_register(
        DOMAIN, SERVICE_SET_SCHEDULE, _handle_set_schedule, SET_SCHEDULE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_SCHEDULE,
        _handle_delete_schedule,
        DELETE_SCHEDULE_SCHEMA,
    )
