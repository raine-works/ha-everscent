# Development

The integration lives in [custom_components/everscent](../custom_components/everscent). Tests are in [tests](../tests).

## Checks

The Python release is pinned in [.python-version](../.python-version).

```sh
pip install -r requirements-test.txt
ruff check .
ruff format --check .
pytest -q
```

The config flow tests need Home Assistant: install `requirements-test-ha.txt` instead and run `pytest -q`. The [Test workflow](../.github/workflows/test.yaml) runs both. The [Validate workflow](../.github/workflows/validate.yaml) runs hassfest and the Marketplace repository validation.

## Releases

The [Release workflow](../.github/workflows/release.yaml) runs after Test passes on `master`. If the `version` in [manifest.json](../custom_components/everscent/manifest.json) has no release yet, it creates the tag `v<version>` with generated notes. To release, bump the version and push.

## Layout

| File | Role |
| :--- | :--- |
| `api.py` | Firebase sign-in and the EverScent API client |
| `coordinator.py` | Polling and token persistence |
| `config_flow.py` | Credentials, token and re-authentication flows |
| `switch.py`, `sensor.py`, `binary_sensor.py`, `button.py`, `number.py` | Entity platforms |
| `services.py`, `services.yaml` | The schedule actions |
