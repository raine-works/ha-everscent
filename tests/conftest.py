"""Test bootstrap.

Two kinds of tests live here:

* ``test_api.py`` — fast unit tests for the HTTP client. They load the
  integration's ``const`` and ``api`` modules directly (below), *without*
  executing the package ``__init__`` (which imports Home Assistant), so they
  need no Home Assistant install.
* ``test_config_flow.py`` — exercises the config flow with a real Home
  Assistant instance via ``pytest-homeassistant-custom-component``. Those tests
  skip themselves when that harness is not installed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

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
