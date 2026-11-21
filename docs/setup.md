# Setup and authentication

Go to Settings → Devices & services → Add integration → EverScent. The first step offers two ways to connect.

## Email and password

Enter your EverScent email and password. The integration signs in with Firebase Authentication, then stores the long-lived refresh token in the config entry. You only sign in once. The password is not stored.

The refresh token is exchanged for a fresh access token automatically. The access token lasts one hour. If Firebase rotates the refresh token, the integration saves the new one.

## Refresh token (advanced)

Choose **Paste a refresh token (advanced)** and paste a Firebase refresh token for your EverScent account. Use this if your account signs in with Google, Apple or Facebook and has no password.

## Social logins

If you sign in with Google, Apple or Facebook and never set a password, email and password sign-in fails. To fix it once:

1. In the EverScent mobile app, use **Forgot password** to set a password on your account.
2. Use that email and password in Home Assistant.

Your social login keeps working in the app.

## One entry per account

Each EverScent account can be added once. Every diffuser on the account becomes a device. See [entities](entities.md).

## Re-authentication

If EverScent rejects the stored token, Home Assistant starts a re-authentication flow. Sign in again with the same account. A different account is refused with "The authenticated account does not match the one being re-authenticated."
