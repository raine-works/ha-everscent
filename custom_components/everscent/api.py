"""API client for the EverScent cloud service.

Authentication is Firebase Authentication (project ``everscent-prod``). A
long-lived Firebase *refresh token* is obtained once at config time and stored
in the config entry; it is exchanged for a short-lived (1 hour) ID token as
needed. The ID token is sent as a Bearer token to the EverScent backend at
``app.everscent.com``.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import quote

from aiohttp import ClientResponseError, ClientSession

from .const import (
    API_BASE,
    FIREBASE_API_KEY,
    FIREBASE_SIGNIN_URL,
    FIREBASE_TOKEN_URL,
    TOKEN_EXPIRY_MARGIN,
)

_LOGGER = logging.getLogger(__name__)


class EverScentAuthError(Exception):
    """Raised when authentication fails (bad credentials or revoked token)."""


class EverScentApiError(Exception):
    """Raised when an EverScent backend request fails."""


class EverScentAuth:
    """Manages Firebase tokens for a single EverScent account."""

    def __init__(self, session: ClientSession, refresh_token: str) -> None:
        """Initialize with a stored Firebase refresh token."""
        self._session = session
        self._refresh_token = refresh_token
        self._id_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def refresh_token(self) -> str:
        """Return the current refresh token (may rotate over time)."""
        return self._refresh_token

    @classmethod
    async def async_login(
        cls, session: ClientSession, email: str, password: str
    ) -> EverScentAuth:
        """Sign in with email/password and return an authenticated instance.

        Firebase accounts that were created purely via a social provider
        (Google/Apple/Facebook) have no password until one is set; those users
        must first set a password in the EverScent app. See the README.
        """
        try:
            async with session.post(
                FIREBASE_SIGNIN_URL,
                params={"key": FIREBASE_API_KEY},
                json={"email": email, "password": password, "returnSecureToken": True},
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    message = data.get("error", {}).get("message", "UNKNOWN")
                    raise EverScentAuthError(message)
        except ClientResponseError as err:
            raise EverScentAuthError(str(err)) from err

        auth = cls(session, data["refreshToken"])
        auth._id_token = data["idToken"]
        auth._expires_at = time.time() + int(data.get("expiresIn", 3600))
        return auth

    async def async_get_id_token(self) -> str:
        """Return a valid ID token, refreshing it if necessary."""
        if self._id_token and time.time() < self._expires_at - TOKEN_EXPIRY_MARGIN:
            return self._id_token
        await self._async_refresh()
        assert self._id_token is not None
        return self._id_token

    async def _async_refresh(self) -> None:
        """Exchange the refresh token for a fresh ID token."""
        try:
            async with self._session.post(
                FIREBASE_TOKEN_URL,
                params={"key": FIREBASE_API_KEY},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    message = data.get("error", {}).get("message", "UNKNOWN")
                    raise EverScentAuthError(message)
        except ClientResponseError as err:
            raise EverScentAuthError(str(err)) from err

        self._id_token = data["id_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 3600))
        # Firebase may rotate the refresh token; keep the newest.
        self._refresh_token = data.get("refresh_token", self._refresh_token)


class EverScentClient:
    """Thin wrapper over the EverScent REST API."""

    def __init__(
        self, session: ClientSession, auth: EverScentAuth, time_zone: str
    ) -> None:
        """Initialize the client.

        ``time_zone`` is an IANA zone name (e.g. ``America/Denver``) required by
        several read endpoints; pass Home Assistant's configured zone.
        """
        self._session = session
        self._auth = auth
        self._time_zone = time_zone

    @property
    def auth(self) -> EverScentAuth:
        """Return the auth helper (to read the possibly-rotated refresh token)."""
        return self._auth

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> Any:
        """Make an authenticated request and return the parsed JSON body."""
        token = await self._auth.async_get_id_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE}/{path}"
        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as resp:
                if resp.status == 401:
                    raise EverScentAuthError("Bearer token rejected (401)")
                if resp.status >= 400:
                    body = await resp.text()
                    raise EverScentApiError(
                        f"{method} {path} failed: {resp.status} {body[:300]}"
                    )
                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()
        except ClientResponseError as err:
            raise EverScentApiError(str(err)) from err

    # --- Reads -------------------------------------------------------------

    async def async_get_user_context(self) -> dict[str, Any]:
        """Return {name, email, phone} for the signed-in user."""
        return await self._request("GET", "User/user-context")

    async def async_get_device_list(self) -> list[dict[str, Any]]:
        """Return the account's devices as [{id, name}, ...]."""
        return await self._request("GET", "Device/dropdown")

    async def async_get_device(self, device_id: int) -> dict[str, Any]:
        """Return the full detail object for one device."""
        tz = quote(self._time_zone, safe="")
        result = await self._request(
            "GET", f"Device?DeviceId={device_id}&TimeZoneId={tz}"
        )
        # The endpoint returns a single-element list.
        if isinstance(result, list):
            if not result:
                raise EverScentApiError(f"Device {device_id} not found")
            return result[0]
        return result

    async def async_get_schedules(self, device_id: int) -> list[dict[str, Any]]:
        """Return the schedule list for one device."""
        return await self._request("GET", f"Schedule/v2?DeviceId={device_id}")

    # --- Writes ------------------------------------------------------------

    async def async_set_power(self, device_id: int, is_active: bool) -> None:
        """Turn a device on (True) or off (False)."""
        await self._request(
            "PATCH",
            f"Device/{device_id}/status",
            json={"isActive": is_active},
        )

    async def async_quick_scent(self, device_id: int) -> None:
        """Trigger a one-off quick-scent burst."""
        await self._request(
            "POST", "Device/quick-scent", json={"deviceId": device_id}
        )

    async def async_acknowledge_empty_bottle(self, device_id: int) -> None:
        """Acknowledge an empty-bottle alert for a device."""
        await self._request(
            "PATCH",
            "Device/acknowledge-empty-bottle",
            json={"deviceId": device_id},
        )

    async def async_set_schedule_active(
        self, device_id: int, schedule_group_id: str, is_active: bool
    ) -> None:
        """Enable or disable a single schedule."""
        await self._request(
            "PATCH",
            "Schedule/v2/status",
            json={
                "deviceId": device_id,
                "scheduleGroupId": schedule_group_id,
                "isActive": is_active,
            },
        )

    async def async_delete_schedule(self, schedule_group_id: str) -> None:
        """Delete a schedule by its group id."""
        await self._request("DELETE", f"Schedule/v2/{schedule_group_id}")

    async def async_create_schedule(self, payload: dict[str, Any]) -> Any:
        """Create a schedule. Payload must include deviceId, days, startTime,
        endTime and a setting (standardSettingId or customSetting)."""
        return await self._request("POST", "Schedule/v2", json=payload)

    async def async_update_schedule(self, payload: dict[str, Any]) -> Any:
        """Update a schedule. Payload must include scheduleGroupId plus the
        same fields as create."""
        return await self._request("PUT", "Schedule/v2", json=payload)
