# Agent guidance for ha-everscent

## Raineworks base rules

This repository follows Raineworks' base rules, in [`.raineworks/base.md`](.raineworks/base.md): read them before
changing anything. They're a copy of `base.md` in `raine-works/agents`, kept current by its sync: change them there,
not here. Where this file is more specific, it wins.

@.raineworks/base.md

## This repository

An unofficial Home Assistant custom integration (`everscent`, "EverScent") for EverScent whole-home HVAC scent
diffusers. It talks to the same undocumented cloud API as the official mobile app, polling every 60 seconds; there is
no local control. It has no Python dependencies beyond Home Assistant (`requirements` is empty). Docs are in
[docs/](docs/README.md): start with [how it works](docs/how-it-works.md).

### Layout

- `custom_components/everscent/`: `api.py` (Firebase sign-in and the EverScent API client, on Home Assistant's aiohttp
  session), `coordinator.py` (polling, and writing a rotated refresh token back to the config entry),
  `config_flow.py` (email and password, or a refresh token; reauth), `entity.py`, the platforms (`switch.py`,
  `sensor.py`, `binary_sensor.py`, `button.py`, `number.py`) and `services.py` with `services.yaml` (the schedule
  actions). Strings are in `strings.json` and `translations/en.json`.
- `tests/`: `test_api.py` (the client, with `aioresponses`) and `test_config_flow.py` (needs Home Assistant).

### Checks and releases

- Two test environments, because `aioresponses` needs an older `aiohttp` than Home Assistant does
  ([docs/development.md](docs/development.md)): `pip install -r requirements-test.txt` then `ruff check .`,
  `ruff format --check .` and `pytest -q` for the API tests; `requirements-test-ha.txt` instead for the config flow
  tests. CI (`test.yaml`, the workflow named `Test`) runs both as separate jobs; `validate.yaml` runs hassfest and HACS
  validation.
- Ruff config is in `pyproject.toml` (line length 88, `E W F I B UP SIM C4`, imports sorted within sections).
- **A release is a version bump:** `release.yaml` runs after `Test` passes on a push to `master` and, when `version`
  in `custom_components/everscent/manifest.json` has no release yet, creates `v<version>`. Bump it in the pull request
  that should release; never tag by hand.

### Rules the code follows

- All I/O is async through `EverScentClient` on `async_get_clientsession`. Setup raises `ConfigEntryAuthFailed` for a
  rejected token and `ConfigEntryNotReady` for other API errors; the coordinator turns a failed poll into
  `UpdateFailed` and user actions fail as `HomeAssistantError` (`translate_api_errors`).
- Credentials: the password is used only at sign-in and never stored; the config entry holds the email and the
  Firebase refresh token, which is never logged (the flow logs errors, not tokens).
- The backend API is undocumented and may change: keep the endpoints in `docs/how-it-works.md` in step with `api.py`.
