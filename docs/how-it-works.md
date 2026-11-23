# How it works

EverScent is a cloud-polling integration. The diffuser only accepts commands relayed through EverScent's cloud. Its Bluetooth is used only for the first Wi-Fi setup. There is no local control.

## Polling

Every 60 seconds the integration fetches the device list, then each device's detail and schedules. After a command it requests a refresh at once.

## Authentication

- Sign-in uses Firebase Authentication (project `everscent-prod`) through the Identity Toolkit REST API.
- The refresh token is exchanged at `securetoken.googleapis.com` for short-lived ID tokens. A token is treated as expired 60 seconds early.
- The ID token is sent to the backend as `Authorization: Bearer`.
- A rotated refresh token is written back to the config entry.
- A rejected token starts re-authentication in Home Assistant.

## Backend

The backend is `https://app.everscent.com/api`. These endpoints are used:

- `GET /User/user-context` to check a refresh token during setup.
- `GET /Device/dropdown`, `GET /Device?DeviceId=&TimeZoneId=` and `GET /Schedule/v2?DeviceId=` to read state.
- `PATCH /Device/{id}/status` for power.
- `POST /Device/quick-scent` for the quick scent.
- `PATCH /Device/acknowledge-empty-bottle`.
- `POST /Schedule/v2` and `PUT /Schedule/v2` to create and update schedules.
- `PATCH /Schedule/v2/status` to enable or disable one.
- `DELETE /Schedule/v2/{scheduleGroupId}`.

The API is undocumented and may change at any time. This project was built by observing the official app's network behavior and is not affiliated with EverScent.

## Errors

When a command fails, Home Assistant shows "Error communicating with EverScent" or asks you to re-authenticate.
