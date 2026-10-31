# EverScent for Home Assistant

An **unofficial** Home Assistant integration for [EverScent](https://everscent.com)
whole-home HVAC scent diffusers. It talks to the same cloud API the EverScent
mobile app uses, so you can see and control your diffuser from Home Assistant.

> This project is not affiliated with or endorsed by EverScent. It was built by
> reverse-engineering the official app's network behavior for personal
> interoperability with hardware the author owns. Use at your own risk; the
> cloud API may change at any time.

## Features

For each diffuser on your account:

- **Power** switch — turn the diffuser on/off (`switch.*_power`)
- **Schedule** switches — enable/disable each configured schedule
- **Sensors** — fragrance name, fragrance level, fragrance category, current
  concentration, firmware version, Wi-Fi network, location
- **Binary sensors** — online, fragrance low, battery low, fan running, light,
  firmware update available
- **Buttons** — quick scent burst, acknowledge empty bottle
- **Services** — `everscent.set_schedule` (create/update) and
  `everscent.delete_schedule`

It is a **cloud-polling** integration (default poll: 60 s). There is no local
control: the diffuser only accepts control commands relayed through EverScent's
cloud. Its Bluetooth is used solely for initial Wi-Fi provisioning.

## Installation (HACS)

1. In HACS → **Custom repositories**, add this repository as an **Integration**.
2. Install **EverScent**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → EverScent**.

Or copy `custom_components/everscent` into your Home Assistant `config/custom_components/` directory manually and restart.

## Authentication

The integration signs in with your EverScent **email and password** using
Firebase Authentication, then stores the long-lived refresh token so you only
log in once. The token is exchanged for a fresh 1-hour access token
automatically; if it is ever revoked, Home Assistant will prompt you to
re-authenticate.

**If you normally sign in with Google, Apple, or Facebook** (and never set a
password), email/password login will fail. Fix it once in the EverScent mobile
app: use **Forgot password** to set a password on your account, then use that
email + password here. Your social login keeps working in the app.

## Services

### `everscent.set_schedule`

Create a schedule (omit `schedule_group_id`) or update one (include it).

```yaml
service: everscent.set_schedule
data:
  device_id: 1864
  days: [1, 2, 3, 4, 5]      # 0 = Sunday ... 6 = Saturday
  start_time: "07:00"
  end_time: "22:00"
  # Either a preset:
  standard_setting_id: 3
  # ...or a custom setting:
  # diffusing_seconds: 20
  # pausing_seconds: 90
  # concentration: 3
```

### `everscent.delete_schedule`

```yaml
service: everscent.delete_schedule
data:
  schedule_group_id: "cfd1535c-1604-43ff-a9ed-7eb3a188024a"
```

The `device_id` and `schedule_group_id` values are visible as attributes on the
schedule switches.

## How it works

- **Auth:** Firebase Authentication, project `everscent-prod`. Login via the
  Identity Toolkit REST API; the refresh token is exchanged at
  `securetoken.googleapis.com` for short-lived ID tokens.
- **Backend:** `https://app.everscent.com/api` (ASP.NET). The ID token is sent
  as `Authorization: Bearer`.
- Key endpoints: `GET /Device/dropdown`, `GET /Device?DeviceId=&TimeZoneId=`,
  `GET /Schedule/v2?DeviceId=`, `PATCH /Device/{id}/status`,
  `POST /Device/quick-scent`, `PATCH /Device/acknowledge-empty-bottle`,
  `POST|PUT /Schedule/v2`, `PATCH /Schedule/v2/status`,
  `DELETE /Schedule/v2/{scheduleGroupId}`.

## License

MIT
