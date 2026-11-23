"""Test bootstrap.

Two kinds of tests live here:

* ``test_api.py`` — fast unit tests for the HTTP client. They load the
  integration's ``const`` and ``api`` modules directly (below), *without*
  executing the package ``__init__`` (which imports Home Assistant), so they
  need no Home Assistant install.
* ``test_config_flow.py``, ``test_services.py``, ``test_coordinator.py`` and
  ``test_entities.py`` — run a real Home Assistant instance via
  ``pytest-homeassistant-custom-component``, using the fixtures at the end of
  this module. Those tests skip themselves when that harness is not installed.
"""

from __future__ import annotations

from collections.abc import Iterator
import copy
import importlib.util
import pathlib
import sys
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BASE = _ROOT / "custom_components" / "everscent"

# Make ``import custom_components.everscent`` work for the Home Assistant tests.
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Register the Home Assistant test plugin only when it is available, so the
# lightweight unit environment (no Home Assistant) still collects cleanly.
try:  # noqa: SIM105
    import pytest_homeassistant_custom_component  # noqa: F401

    pytest_plugins = ("pytest_homeassistant_custom_component",)
except ImportError:
    pass


# Register a lightweight stand-in package so ``from .const import ...`` inside
# api.py resolves to the module we load below, bypassing the real __init__.
_pkg = types.ModuleType("everscent_under_test")
_pkg.__path__ = [str(_BASE)]
sys.modules["everscent_under_test"] = _pkg


def _load(mod_name: str, filename: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(mod_name, _BASE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


_load("everscent_under_test.const", "const.py")
_load("everscent_under_test.api", "api.py")


# Fixtures for the Home Assistant tests. Home Assistant is imported inside
# them, so this module still loads in the environment without it.

DEVICE_ID = 1864
DETAIL: dict[str, Any] = {
    "id": DEVICE_ID,
    "deviceName": "Hallway",
    "isActive": True,
    "status": 1,
    "fragrance": {
        "fragranceLevel": 72,
        "displayName": "Linen",
        "category": "Fresh",
        "isFragranceLow": False,
    },
    "currentSchedule": {"concentrationLevel": 2},
    "isBatteryLow": True,
    "isFanActive": True,
    "isLightOn": False,
    "version": "1.2.3",
    "macId": "aa:bb:cc:dd:ee:ff",
}
SCHEDULES: list[dict[str, Any]] = [
    {
        "scheduleGroupId": "group-1",
        "isActive": True,
        "days": [1, 2, 3],
        "startTime": "07:00",
        "endTime": "22:00",
        "customSetting": {"diffusing": 20, "pausing": 90, "concentration": 3},
    }
]


@pytest.fixture
def mock_client() -> Iterator[AsyncMock]:
    """Replace EverScentClient and EverScentAuth with mocks for one device.

    The client returns ``DETAIL`` and ``SCHEDULES`` for device ``DEVICE_ID``;
    ``client.auth.refresh_token`` starts as the entry's token, ``"refresh"``.
    """
    client = AsyncMock()
    client.auth = MagicMock(refresh_token="refresh")
    client.async_get_device_list.return_value = [{"id": DEVICE_ID}]
    client.async_get_device.return_value = copy.deepcopy(DETAIL)
    client.async_get_schedules.return_value = copy.deepcopy(SCHEDULES)
    with (
        patch("custom_components.everscent.EverScentClient", return_value=client),
        patch("custom_components.everscent.EverScentAuth") as auth,
    ):
        auth.return_value.async_get_id_token = AsyncMock(return_value="id")
        yield client


@pytest.fixture
def config_entry() -> Any:
    """Return an EverScent config entry holding the token ``"refresh"``."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.everscent.const import CONF_REFRESH_TOKEN, DOMAIN

    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="user@example.com",
        data={"email": "user@example.com", CONF_REFRESH_TOKEN: "refresh"},
    )


@pytest.fixture
async def init_integration(
    hass: Any, enable_custom_integrations: None, config_entry: Any, mock_client: Any
) -> Any:
    """Set up the integration with ``mock_client`` and return its entry."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
