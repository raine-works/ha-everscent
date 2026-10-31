"""Number platform for EverScent (quick-scent duration)."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    QUICK_SCENT_DEFAULT_DURATION,
    QUICK_SCENT_MAX_DURATION,
    QUICK_SCENT_MIN_DURATION,
)
from .coordinator import EverScentConfigEntry, EverScentDataUpdateCoordinator
from .entity import EverScentEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverScentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EverScent number entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        EverScentQuickScentDurationNumber(coordinator, device_id)
        for device_id in coordinator.data
    )


class EverScentQuickScentDurationNumber(EverScentEntity, RestoreNumber):
    """How long the quick-scent button runs, in seconds.

    The cloud has no stored setting for this; it is sent with each quick-scent
    request, so the value is kept locally and restored across restarts.
    """

    _attr_translation_key = "quick_scent_duration"
    _attr_icon = "mdi:timer-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = QUICK_SCENT_MIN_DURATION
    _attr_native_max_value = QUICK_SCENT_MAX_DURATION
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(
        self, coordinator: EverScentDataUpdateCoordinator, device_id: int
    ) -> None:
        """Initialize the duration number."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_quick_scent_duration"

    async def async_added_to_hass(self) -> None:
        """Restore the last chosen duration."""
        await super().async_added_to_hass()
        value = QUICK_SCENT_DEFAULT_DURATION
        if (last := await self.async_get_last_number_data()) is not None and (
            last.native_value is not None
        ):
            value = int(last.native_value)
        self._store(value)

    @property
    def native_value(self) -> float:
        """Return the current duration."""
        return self.coordinator.quick_scent_durations.get(
            self._device_id, QUICK_SCENT_DEFAULT_DURATION
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set a new duration."""
        self._store(int(value))
        self.async_write_ha_state()

    def _store(self, value: int) -> None:
        """Clamp and save the duration where the button can read it."""
        self.coordinator.quick_scent_durations[self._device_id] = max(
            QUICK_SCENT_MIN_DURATION, min(QUICK_SCENT_MAX_DURATION, value)
        )
