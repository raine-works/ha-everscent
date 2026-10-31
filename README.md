# EverScent for Home Assistant

An **unofficial** [Home Assistant](https://www.home-assistant.io/) integration for
[EverScent](https://everscent.com) whole-home HVAC scent diffusers, from
[raine-works](https://github.com/raine-works). It talks to the same cloud API the
EverScent mobile app uses, so you can see and control your diffuser from Home
Assistant.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg?style=for-the-badge)](LICENSE)

[![Test](https://github.com/raine-works/ha-everscent/actions/workflows/test.yaml/badge.svg)](https://github.com/raine-works/ha-everscent/actions/workflows/test.yaml)
[![Validate](https://github.com/raine-works/ha-everscent/actions/workflows/validate.yaml/badge.svg)](https://github.com/raine-works/ha-everscent/actions/workflows/validate.yaml)

<a href="https://buymeacoffee.com/raineworks"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy Me a Coffee" /></a>

> This project is not affiliated with, authorized, or endorsed by EverScent. It
> was built by observing the official app's own network behavior, for personal
> interoperability with hardware you own. Use at your own risk — the cloud API is
> undocumented and may change at any time.

## Features

For each diffuser on your account:

- **Power** switch — turn the diffuser on/off
- **Schedule** switches — enable/disable each configured schedule
- **Sensors** — fragrance name, fragrance level, fragrance category, current
  concentration, firmware version, Wi-Fi network, location
- **Binary sensors** — online, fragrance low, battery low, fan running, light,
  firmware update available
- **Buttons** — quick scent burst, acknowledge empty bottle
- **Quick scent duration** number — how long the quick scent button runs
  (5–120 s, default 30 s)
- **Services** — `everscent.set_schedule` (create/update) and
  `everscent.delete_schedule`

It is a **cloud-polling** integration (default poll: 60 s). There is no local
control: the diffuser only accepts commands relayed through EverScent's cloud,
and its Bluetooth is used solely for initial Wi-Fi provisioning.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=raine-works&repository=ha-everscent&category=integration)

1. Click the button above (or in HACS, **⋮ → Custom repositories**, add
   `https://github.com/raine-works/ha-everscent` as category **Integration**).
2. Install **EverScent**, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → EverScent**.

### Manual

Copy `custom_components/everscent` into your Home Assistant
`config/custom_components/` directory and restart.

## Authentication

The integration signs in with your EverScent **email and password** using
Firebase Authentication, then stores the long-lived refresh token so you only log
in once. The token is exchanged for a fresh 1-hour access token automatically; if
it is ever revoked, Home Assistant will prompt you to re-authenticate.

**If you sign in with Google, Apple, or Facebook** (and never set a password),
email/password login will fail. Fix it once in the EverScent mobile app: use
**Forgot password** to set a password on your account, then use that email +
password here. Your social login keeps working in the app.

## Services

### `everscent.set_schedule`

Create a schedule (omit `schedule_group_id`) or update one (include it).

```yaml
service: everscent.set_schedule
data:
  device_id: 1864              # your EverScent device id (see schedule switch attributes)
  days: [1, 2, 3, 4, 5]        # 0 = Sunday ... 6 = Saturday
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

The `device_id` and `schedule_group_id` values are exposed as attributes on the
schedule switches.

## How it works

- **Auth:** Firebase Authentication (project `everscent-prod`). Login via the
  Identity Toolkit REST API; the refresh token is exchanged at
  `securetoken.googleapis.com` for short-lived ID tokens.
- **Backend:** `https://app.everscent.com/api` (ASP.NET). The ID token is sent as
  `Authorization: Bearer`.
- Key endpoints: `GET /Device/dropdown`, `GET /Device?DeviceId=&TimeZoneId=`,
  `GET /Schedule/v2?DeviceId=`, `PATCH /Device/{id}/status`,
  `POST /Device/quick-scent`, `PATCH /Device/acknowledge-empty-bottle`,
  `POST|PUT /Schedule/v2`, `PATCH /Schedule/v2/status`,
  `DELETE /Schedule/v2/{scheduleGroupId}`.

## Contributing

Issues and PRs welcome. This is a community project maintained on a best-effort
basis; the API is undocumented, so behavior may vary across firmware or app
versions. If something breaks, please include your diffuser's firmware version
(see the Firmware version sensor) and any relevant Home Assistant logs.

## ☕ Support

If you find this project helpful, consider buying me a coffee to support continued
maintenance and development:

<a href="https://buymeacoffee.com/raineworks"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy Me a Coffee" /></a>

## License

[MIT](LICENSE) © [Raine Petersen](https://github.com/raine-works)
