"""Button platform for EverScent (quick scent, acknowledge empty bottle)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import QUICK_SCENT_DEFAULT_DURATION
from .coordinator import EverScentConfigEntry, EverScentDataUpdateCoordinator
from .entity import EverScentEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverScentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up buttons for each device."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []
    for device_id in coordinator.data:
        entities.append(EverScentQuickScentButton(coordinator, device_id))
        entities.append(EverScentAcknowledgeBottleButton(coordinator, device_id))
    async_add_entities(entities)


class EverScentQuickScentButton(EverScentEntity, ButtonEntity):
    """Trigger a one-off quick scent burst."""

    _attr_translation_key = "quick_scent"
    _attr_icon = "mdi:spray"

    def __init__(
        self, coordinator: EverScentDataUpdateCoordinator, device_id: int
    ) -> None:
        """Initialize the quick-scent button."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_quick_scent"

    async def async_press(self) -> None:
        """Fire a quick scent for the configured duration."""
        duration = self.coordinator.quick_scent_durations.get(
            self._device_id, QUICK_SCENT_DEFAULT_DURATION
        )
        await self.coordinator.client.async_quick_scent(self._device_id, duration)


class EverScentAcknowledgeBottleButton(EverScentEntity, ButtonEntity):
    """Acknowledge an empty-bottle alert."""

    _attr_translation_key = "acknowledge_empty_bottle"
    _attr_icon = "mdi:check-circle"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: EverScentDataUpdateCoordinator, device_id: int
    ) -> None:
        """Initialize the acknowledge button."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_ack_empty_bottle"

    async def async_press(self) -> None:
        """Acknowledge the empty bottle."""
        await self.coordinator.client.async_acknowledge_empty_bottle(self._device_id)
        await self.coordinator.async_request_refresh()
