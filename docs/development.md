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

The Home Assistant tests (config flow, setup and polling, entities, actions) need Home Assistant: install `requirements-test-ha.txt` instead and run `pytest -q`. They mock `EverScentClient` with the fixtures in [tests/conftest.py](../tests/conftest.py). The [Test workflow](../.github/workflows/test.yaml) runs both. The [Validate workflow](../.github/workflows/validate.yaml) runs hassfest and the Marketplace repository validation.

## Releases

On every push to `master`, the [Release pull request workflow](../.github/workflows/release-pr.yml) keeps one pull request, `Release v<version>`, open with the next version in [manifest.json](../custom_components/everscent/manifest.json): major for a breaking change (`type!:`), minor for a `feat`, patch for anything else that changes `custom_components/`. To release, merge it. The [Release workflow](../.github/workflows/release.yaml) then runs after Test passes and creates the tag `v<version>` with generated notes. Don't bump the version by hand.

## Layout

| File | Role |
| :--- | :--- |
| `api.py` | Firebase sign-in and the EverScent API client |
| `coordinator.py` | Polling and token persistence |
| `config_flow.py` | Credentials, token and re-authentication flows |
| `switch.py`, `sensor.py`, `binary_sensor.py`, `button.py`, `number.py` | Entity platforms |
| `services.py`, `services.yaml` | The schedule actions |
