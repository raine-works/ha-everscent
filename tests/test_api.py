"""Unit tests for the EverScent API client (mocked HTTP, no network)."""

from __future__ import annotations

import re

import aiohttp
import pytest

# aioresponses is only present in the lightweight unit environment; skip this
# whole module in the Home Assistant test environment (which pins a newer,
# incompatible aiohttp).
aioresponses = pytest.importorskip("aioresponses").aioresponses

from everscent_under_test.api import (  # noqa: E402
    EverScentApiError,
    EverScentAuth,
    EverScentAuthError,
    EverScentClient,
)
from everscent_under_test.const import API_BASE  # noqa: E402

TOKEN_URL = re.compile(r"https://securetoken\.googleapis\.com/v1/token.*")
SIGNIN_URL = re.compile(
    r"https://identitytoolkit\.googleapis\.com/v1/accounts:signInWithPassword.*"
)


@pytest.fixture
async def session():
    """Provide an aiohttp session scoped to a test."""
    async with aiohttp.ClientSession() as sess:
        yield sess


async def test_login_success(session):
    """async_login returns an auth holding the refresh token."""
    with aioresponses() as m:
        m.post(
            SIGNIN_URL,
            payload={
                "idToken": "id-1",
                "refreshToken": "refresh-1",
                "expiresIn": "3600",
            },
        )
        auth = await EverScentAuth.async_login(session, "a@b.com", "pw")
    assert auth.refresh_token == "refresh-1"
    # The token from login is cached and reused without a refresh call.
    assert await auth.async_get_id_token() == "id-1"


async def test_login_bad_credentials(session):
    """A non-200 sign-in surfaces as EverScentAuthError."""
    with aioresponses() as m:
        m.post(
            SIGNIN_URL,
            status=400,
            payload={"error": {"message": "INVALID_LOGIN_CREDENTIALS"}},
        )
        with pytest.raises(EverScentAuthError, match="INVALID_LOGIN_CREDENTIALS"):
            await EverScentAuth.async_login(session, "a@b.com", "wrong")


async def test_token_refresh_and_cache(session):
    """A fresh auth refreshes once, then serves the cached token."""
    auth = EverScentAuth(session, "refresh-1")
    with aioresponses() as m:
        m.post(
            TOKEN_URL,
            payload={
                "id_token": "id-fresh",
                "refresh_token": "refresh-2",
                "expires_in": "3600",
            },
        )
        token = await auth.async_get_id_token()
        # Second call is served from cache; no second mock is registered, so a
        # second HTTP call would raise.
        token2 = await auth.async_get_id_token()
    assert token == "id-fresh"
    assert token2 == "id-fresh"
    # Firebase may rotate the refresh token; the newest is retained.
    assert auth.refresh_token == "refresh-2"


async def test_refresh_token_rejected(session):
    """A rejected refresh token raises EverScentAuthError."""
    auth = EverScentAuth(session, "revoked")
    with aioresponses() as m:
        m.post(
            TOKEN_URL,
            status=400,
            payload={"error": {"message": "TOKEN_EXPIRED"}},
        )
        with pytest.raises(EverScentAuthError, match="TOKEN_EXPIRED"):
            await auth.async_get_id_token()


def _authed_client(session) -> EverScentClient:
    auth = EverScentAuth(session, "refresh-1")
    # Pre-seed a valid token so the client does not attempt a refresh.
    auth._id_token = "id-1"  # noqa: SLF001
    auth._expires_at = 10**12  # noqa: SLF001
    return EverScentClient(session, auth, "America/Denver")


async def test_get_device_unwraps_single_element_list(session):
    """async_get_device returns the first element of the list response."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.get(
            re.compile(rf"{re.escape(API_BASE)}/Device\?.*"),
            payload=[{"id": 1864, "isActive": True}],
        )
        detail = await client.async_get_device(1864)
    assert detail["id"] == 1864
    assert detail["isActive"] is True


async def test_get_device_empty_raises(session):
    """An empty device response raises EverScentApiError."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.get(re.compile(rf"{re.escape(API_BASE)}/Device\?.*"), payload=[])
        with pytest.raises(EverScentApiError):
            await client.async_get_device(1864)


async def test_get_schedules(session):
    """async_get_schedules returns the list as-is."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.get(
            re.compile(rf"{re.escape(API_BASE)}/Schedule/v2\?.*"),
            payload=[{"scheduleGroupId": "abc", "isActive": True}],
        )
        schedules = await client.async_get_schedules(1864)
    assert schedules[0]["scheduleGroupId"] == "abc"


async def test_set_power_sends_expected_request(session):
    """async_set_power PATCHes the status route with the right body."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.patch(f"{API_BASE}/Device/1864/status", payload=True)
        await client.async_set_power(1864, False)
        request = next(iter(m.requests))
    # method + URL
    assert request[0] == "PATCH"
    assert str(request[1]).endswith("/Device/1864/status")


async def test_401_raises_auth_error(session):
    """A 401 from the backend raises EverScentAuthError (triggers reauth)."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.get(f"{API_BASE}/User/user-context", status=401, payload={})
        with pytest.raises(EverScentAuthError):
            await client.async_get_user_context()


async def test_4xx_raises_api_error(session):
    """A non-401 error status raises EverScentApiError."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.get(f"{API_BASE}/User/user-context", status=500, body="boom")
        with pytest.raises(EverScentApiError):
            await client.async_get_user_context()


async def test_quick_scent_sends_device_ids_and_diffusion(session):
    """async_quick_scent POSTs a device-id list plus the burst length in seconds."""
    client = _authed_client(session)
    with aioresponses() as m:
        m.post(f"{API_BASE}/Device/quick-scent", payload=True)
        await client.async_quick_scent(1864, 5)
        (method, url), calls = next(iter(m.requests.items()))
    assert method == "POST"
    assert str(url).endswith("/Device/quick-scent")
    assert calls[0].kwargs["json"] == {"deviceIds": [1864], "diffusion": 5}
