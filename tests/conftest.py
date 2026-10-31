"""Test bootstrap.

Loads the integration's ``const`` and ``api`` modules directly from the
``custom_components/everscent`` package *without* executing the package
``__init__`` (which imports Home Assistant). This keeps the ``api.py`` unit
tests fast and dependency-light: they exercise the real client code against a
mocked HTTP layer, with no Home Assistant install required.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

_BASE = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "everscent"

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
