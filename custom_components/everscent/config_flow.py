"""Config flow for EverScent.

Two ways to authenticate:

* **credentials** — email + password (Firebase email/password sign-in).
* **token** — paste a Firebase refresh token. Useful for accounts that only
  ever sign in with Google/Apple/Facebook and have no password.

Either path ends up storing the long-lived refresh token in the config entry.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import (
    EverScentApiError,
    EverScentAuth,
    EverScentAuthError,
    EverScentClient,
)
from .const import CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

TOKEN_SCHEMA = vol.Schema({vol.Required(CONF_REFRESH_TOKEN): str})


class EverScentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the EverScent config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick an authentication method."""
        return self.async_show_menu(
            step_id="user", menu_options=["credentials", "token"]
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Re-authentication reuses the same method menu."""
        return self.async_show_menu(
            step_id="user", menu_options=["credentials", "token"]
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authenticate with email and password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            email = user_input[CONF_EMAIL]
            try:
                auth = await EverScentAuth.async_login(
                    session, email, user_input[CONF_PASSWORD]
                )
            except EverScentAuthError as err:
                _LOGGER.debug("EverScent login failed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                return await self._async_finish(email, auth.refresh_token)

        return self.async_show_form(
            step_id="credentials", data_schema=CREDENTIALS_SCHEMA, errors=errors
        )

    async def async_step_token(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authenticate by pasting a Firebase refresh token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            token = user_input[CONF_REFRESH_TOKEN].strip()
            auth = EverScentAuth(session, token)
            try:
                await auth.async_get_id_token()
                client = EverScentClient(
                    session, auth, self.hass.config.time_zone or "UTC"
                )
                context = await client.async_get_user_context()
            except (EverScentAuthError, EverScentApiError) as err:
                _LOGGER.debug("EverScent token validation failed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                email = context.get("email") or "EverScent account"
                return await self._async_finish(email, auth.refresh_token)

        return self.async_show_form(
            step_id="token", data_schema=TOKEN_SCHEMA, errors=errors
        )

    async def _async_finish(self, email: str, refresh_token: str) -> ConfigFlowResult:
        """Create or (on reauth) update the entry for this account."""
        await self.async_set_unique_id(email.lower())
        data = {CONF_EMAIL: email, CONF_REFRESH_TOKEN: refresh_token}

        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data=data
            )

        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=email, data=data)
