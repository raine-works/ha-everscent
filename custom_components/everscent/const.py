"""Constants for the EverScent integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "everscent"

# Firebase project configuration, extracted from the official EverScent iOS app
# (GoogleService-Info.plist, project "everscent-prod"). The Web API key is a
# public client identifier, embedded in the shipping app by design.
FIREBASE_API_KEY = "AIzaSyCA5vHyp-Qp3EodfnUPd4DnQ6S9cdGtXLw"
FIREBASE_PROJECT_ID = "everscent-prod"

# Firebase Identity Toolkit / Secure Token REST endpoints.
FIREBASE_SIGNIN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)
FIREBASE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

# EverScent application backend.
API_BASE = "https://app.everscent.com/api"

# Config entry storage keys.
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EMAIL = "email"

# How often to poll the cloud for device state.
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

# Treat an ID token as expired this many seconds before its real expiry, to
# avoid races where a request is sent with a token about to expire.
TOKEN_EXPIRY_MARGIN = 60
