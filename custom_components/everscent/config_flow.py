"""Config flow for EverScent."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EverScentAuth, EverScentAuthError
from .const import CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class EverScentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the EverScent config flow (email/password -> refresh token)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial login step."""
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
                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_REFRESH_TOKEN: auth.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the stored token is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a fresh password."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        email = reauth_entry.data[CONF_EMAIL]

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                auth = await EverScentAuth.async_login(
                    session, email, user_input[CONF_PASSWORD]
                )
            except EverScentAuthError:
                errors["base"] = "invalid_auth"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={
                        CONF_EMAIL: email,
                        CONF_REFRESH_TOKEN: auth.refresh_token,
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": email},
            errors=errors,
        )
