"""Binary sensor platform for EverScent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EverScentConfigEntry
from .entity import EverScentEntity


@dataclass(frozen=True, kw_only=True)
class EverScentBinaryDescription(BinarySensorEntityDescription):
    """Describes an EverScent binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool]


def _fragrance(detail: dict[str, Any]) -> dict[str, Any]:
    return detail.get("fragrance") or {}


BINARY_SENSORS: tuple[EverScentBinaryDescription, ...] = (
    EverScentBinaryDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        # status == 1 means the device is reporting as online.
        value_fn=lambda d: d.get("status") == 1,
    ),
    EverScentBinaryDescription(
        key="fragrance_low",
        translation_key="fragrance_low",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: bool(_fragrance(d).get("isFragranceLow")),
    ),
    EverScentBinaryDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda d: bool(d.get("isBatteryLow")),
    ),
    EverScentBinaryDescription(
        key="fan_active",
        translation_key="fan_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: bool(d.get("isFanActive")),
    ),
    EverScentBinaryDescription(
        key="light_on",
        translation_key="light_on",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda d: bool(d.get("isLightOn")),
    ),
    EverScentBinaryDescription(
        key="update_available",
        translation_key="update_available",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_registry_enabled_default=False,
        value_fn=lambda d: bool(d.get("isUpdateAvailable")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverScentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors for each device."""
    coordinator = entry.runtime_data
    async_add_entities(
        EverScentBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
    )


class EverScentBinarySensor(EverScentEntity, BinarySensorEntity):
    """A boolean reading from device detail."""

    entity_description: EverScentBinaryDescription

    def __init__(
        self, coordinator, device_id: int, description: EverScentBinaryDescription
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the boolean state."""
        return self.entity_description.value_fn(self._detail)
