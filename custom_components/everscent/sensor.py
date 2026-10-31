"""Sensor platform for EverScent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import EverScentConfigEntry
from .entity import EverScentEntity


@dataclass(frozen=True, kw_only=True)
class EverScentSensorDescription(SensorEntityDescription):
    """Describes an EverScent sensor and how to read it from device detail."""

    value_fn: Callable[[dict[str, Any]], Any]


def _fragrance(detail: dict[str, Any]) -> dict[str, Any]:
    return detail.get("fragrance") or {}


SENSORS: tuple[EverScentSensorDescription, ...] = (
    EverScentSensorDescription(
        key="fragrance_level",
        translation_key="fragrance_level",
        icon="mdi:cup-water",
        value_fn=lambda d: _fragrance(d).get("fragranceLevel"),
    ),
    EverScentSensorDescription(
        key="fragrance_name",
        translation_key="fragrance_name",
        icon="mdi:flower",
        value_fn=lambda d: _fragrance(d).get("displayName")
        or _fragrance(d).get("name"),
    ),
    EverScentSensorDescription(
        key="fragrance_category",
        translation_key="fragrance_category",
        icon="mdi:shape",
        value_fn=lambda d: _fragrance(d).get("category"),
    ),
    EverScentSensorDescription(
        key="concentration",
        translation_key="concentration",
        icon="mdi:air-filter",
        value_fn=lambda d: (d.get("currentSchedule") or {}).get("concentrationLevel"),
    ),
    EverScentSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("version"),
    ),
    EverScentSensorDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        icon="mdi:wifi",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("wifiSSID"),
    ),
    EverScentSensorDescription(
        key="location",
        translation_key="location",
        icon="mdi:map-marker",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("locationName"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverScentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors for each device."""
    coordinator = entry.runtime_data
    async_add_entities(
        EverScentSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    )


class EverScentSensor(EverScentEntity, SensorEntity):
    """A sensor reading one field from device detail."""

    entity_description: EverScentSensorDescription

    def __init__(
        self, coordinator, device_id: int, description: EverScentSensorDescription
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self._detail)
