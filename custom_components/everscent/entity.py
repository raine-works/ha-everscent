"""Base entity for EverScent."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EverScentDataUpdateCoordinator


class EverScentEntity(CoordinatorEntity[EverScentDataUpdateCoordinator]):
    """Base class for entities tied to a single EverScent device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: EverScentDataUpdateCoordinator, device_id: int
    ) -> None:
        """Initialize the entity for a device id."""
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def _detail(self) -> dict[str, Any]:
        """Return the current device detail dict."""
        return self.coordinator.data[self._device_id]["detail"]

    @property
    def _schedules(self) -> list[dict[str, Any]]:
        """Return the current schedule list."""
        return self.coordinator.data[self._device_id]["schedules"]

    @property
    def available(self) -> bool:
        """Return True if the device is present in the latest poll."""
        return (
            super().available
            and self.coordinator.data is not None
            and self._device_id in self.coordinator.data
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        detail = self._detail
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=detail.get("deviceName") or detail.get("displayName"),
            manufacturer="EverScent",
            model="Whole Home Diffuser",
            sw_version=detail.get("version"),
            connections=(
                {("mac", detail["macId"])} if detail.get("macId") else set()
            ),
        )
