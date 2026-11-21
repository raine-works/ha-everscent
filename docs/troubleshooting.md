# Troubleshooting

## Sign-in fails with "Could not authenticate"

- Check the email and password.
- If you only use Google, Apple or Facebook, set a password in the EverScent app first. See [setup](setup.md).
- Or paste a refresh token instead.

## "Could not connect to the EverScent service"

Home Assistant could not reach EverScent's cloud. Try again later. Everything here depends on the cloud.

## Home Assistant asks to re-authenticate

EverScent rejected the stored token, for example after a password change. Sign in again with the same account.

## Values look stale

Data refreshes every 60 seconds. Commands refresh right away, except the quick scent button, which waits for the next poll.

## Fragrance level never changes

Fragrance level is passed through from the cloud as is. Use the Fragrance low binary sensor to know when to replace the bottle. See [entities](entities.md).

## An entity is missing

Firmware version, Wi-Fi network, Location, Firmware update available and Acknowledge empty bottle are disabled by default. Enable them from the device's entity list.

## Reporting a problem

Open an issue at [github.com/raine-works/ha-everscent/issues](https://github.com/raine-works/ha-everscent/issues). Include the Firmware version and the relevant Home Assistant logs.
