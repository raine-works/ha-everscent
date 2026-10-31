"""Switch platform for EverScent (device power + per-schedule enable)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EverScentConfigEntry, EverScentDataUpdateCoordinator
from .entity import EverScentEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverScentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches for each device and its schedules."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    for device_id in coordinator.data:
        entities.append(EverScentPowerSwitch(coordinator, device_id))
        for schedule in coordinator.data[device_id]["schedules"]:
            entities.append(
                EverScentScheduleSwitch(
                    coordinator, device_id, schedule["scheduleGroupId"]
                )
            )
    async_add_entities(entities)


class EverScentPowerSwitch(EverScentEntity, SwitchEntity):
    """Master on/off for a diffuser."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "power"

    def __init__(
        self, coordinator: EverScentDataUpdateCoordinator, device_id: int
    ) -> None:
        """Initialize the power switch."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_power"

    @property
    def is_on(self) -> bool:
        """Return whether the diffuser is active."""
        return bool(self._detail.get("isActive"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the diffuser on."""
        await self.coordinator.client.async_set_power(self._device_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the diffuser off."""
        await self.coordinator.client.async_set_power(self._device_id, False)
        await self.coordinator.async_request_refresh()


class EverScentScheduleSwitch(EverScentEntity, SwitchEntity):
    """Enable/disable a single schedule on a diffuser."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: EverScentDataUpdateCoordinator,
        device_id: int,
        schedule_group_id: str,
    ) -> None:
        """Initialize the schedule switch."""
        super().__init__(coordinator, device_id)
        self._group_id = schedule_group_id
        self._attr_unique_id = f"{device_id}_schedule_{schedule_group_id}"

    @property
    def _schedule(self) -> dict[str, Any] | None:
        """Return this switch's schedule entry, if it still exists."""
        for schedule in self._schedules:
            if schedule["scheduleGroupId"] == self._group_id:
                return schedule
        return None

    @property
    def available(self) -> bool:
        """Available only while the schedule exists."""
        return super().available and self._schedule is not None

    @property
    def name(self) -> str:
        """Return a human label derived from the schedule window."""
        schedule = self._schedule or {}
        start = schedule.get("startTime", "??:??")
        end = schedule.get("endTime", "??:??")
        return f"Schedule {start}-{end}"

    @property
    def is_on(self) -> bool:
        """Return whether the schedule is active."""
        schedule = self._schedule
        return bool(schedule and schedule.get("isActive"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the schedule's details as attributes."""
        schedule = self._schedule or {}
        setting = schedule.get("standardSetting") or schedule.get("customSetting") or {}
        return {
            "schedule_group_id": self._group_id,
            "days": schedule.get("days"),
            "start_time": schedule.get("startTime"),
            "end_time": schedule.get("endTime"),
            "diffusing_seconds": setting.get("diffusing"),
            "pausing_seconds": setting.get("pausing"),
            "concentration": setting.get("concentration"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the schedule."""
        await self.coordinator.client.async_set_schedule_active(
            self._device_id, self._group_id, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the schedule."""
        await self.coordinator.client.async_set_schedule_active(
            self._device_id, self._group_id, False
        )
        await self.coordinator.async_request_refresh()
