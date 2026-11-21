<p align="center"><img src="custom_components/everscent/brand/icon.png" alt="EverScent" width="128" /></p>

# EverScent for Home Assistant

An **unofficial** [Home Assistant](https://www.home-assistant.io/) integration for
[EverScent](https://everscent.com) whole-home HVAC scent diffusers, from
[raine-works](https://github.com/raine-works). It talks to the same cloud API the
EverScent mobile app uses, so you can see and control your diffuser from Home
Assistant.

[![Home Assistant Marketplace](https://img.shields.io/badge/Home_Assistant-Marketplace-41BDF5.svg?style=for-the-badge)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=raine-works&repository=ha-everscent&category=integration)
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

- A **power** switch, and a switch for each schedule
- **Sensors** for the fragrance, its category, the concentration and more
- **Binary sensors** for online, fragrance low, battery low, fan and light
- A **quick scent** button with an adjustable duration
- **Actions** to create, update and delete schedules

It is a cloud-polling integration (every 60 seconds). There is no local control.

## Installation

[![Open your Home Assistant instance and open this repository in the Home Assistant Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=raine-works&repository=ha-everscent&category=integration)

1. Click the button above, or open Settings → Marketplace. If EverScent is not listed, add `https://github.com/raine-works/ha-everscent` as a custom repository of type Integration.
2. Download **EverScent** and restart Home Assistant.
3. Go to Settings → Devices & services → Add integration → EverScent.

To install by hand, see [Installation](docs/installation.md).

## Documentation

| Guide | What it covers |
| :--- | :--- |
| [Installation](docs/installation.md) | The Marketplace or a manual install |
| [Setup and authentication](docs/setup.md) | Signing in, social logins, re-authentication |
| [Entities](docs/entities.md) | Every entity and what it means |
| [Actions](docs/actions.md) | `everscent.set_schedule` and `everscent.delete_schedule` |
| [How it works](docs/how-it-works.md) | Cloud polling and the API |
| [Troubleshooting](docs/troubleshooting.md) | Common problems |
| [Development](docs/development.md) | Tests, lint and releases |

## Contributing

Issues and PRs welcome. This is a community project maintained on a best-effort
basis; the API is undocumented, so behavior may vary across firmware or app
versions. If something breaks, please include your diffuser's firmware version
(see the Firmware version sensor) and any relevant Home Assistant logs.

## Support

If you find this project helpful, consider buying me a coffee to support continued
maintenance and development:

<a href="https://buymeacoffee.com/raineworks"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black" alt="Buy Me a Coffee" /></a>

## License

[MIT](LICENSE) © [Raine Petersen](https://github.com/raine-works)
