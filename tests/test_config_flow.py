"""Config flow tests (require pytest-homeassistant-custom-component)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import SOURCE_USER  # noqa: E402
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from pytest_homeassistant_custom_component.test_util.aiohttp import (  # noqa: E402
    AiohttpClientMocker,
)

from custom_components.everscent.const import (  # noqa: E402
    API_BASE,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    FIREBASE_SIGNIN_URL,
    FIREBASE_TOKEN_URL,
)

SETUP = "custom_components.everscent.async_setup_entry"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the custom integration during tests."""
    return


async def _start_user_flow(hass: HomeAssistant, step: str) -> dict:
    """Open the flow and select a menu option, returning the next step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": step}
    )


async def test_credentials_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Email/password login creates an entry with the refresh token."""
    aioclient_mock.post(
        FIREBASE_SIGNIN_URL,
        json={"idToken": "id", "refreshToken": "refresh-xyz", "expiresIn": "3600"},
    )
    result = await _start_user_flow(hass, "credentials")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "credentials"

    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "pw"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "user@example.com"
    assert result["data"][CONF_REFRESH_TOKEN] == "refresh-xyz"


async def test_credentials_invalid_auth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Bad credentials show an error on the form."""
    aioclient_mock.post(
        FIREBASE_SIGNIN_URL,
        status=400,
        json={"error": {"message": "INVALID_LOGIN_CREDENTIALS"}},
    )
    result = await _start_user_flow(hass, "credentials")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "wrong"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_token_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Pasting a refresh token validates it and creates an entry."""
    aioclient_mock.post(
        FIREBASE_TOKEN_URL,
        json={
            "id_token": "id",
            "refresh_token": "refresh-xyz",
            "expires_in": "3600",
        },
    )
    aioclient_mock.get(
        f"{API_BASE}/User/user-context",
        json={"name": "Raine", "email": "user@example.com", "phone": "1"},
    )
    result = await _start_user_flow(hass, "token")
    assert result["step_id"] == "token"

    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_REFRESH_TOKEN: "refresh-xyz"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "user@example.com"
    assert result["result"].unique_id == "user@example.com"


async def test_token_flow_invalid(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A rejected refresh token shows an error."""
    aioclient_mock.post(
        FIREBASE_TOKEN_URL,
        status=400,
        json={"error": {"message": "TOKEN_EXPIRED"}},
    )
    result = await _start_user_flow(hass, "token")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_REFRESH_TOKEN: "revoked"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
