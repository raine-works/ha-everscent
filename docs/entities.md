# Entities

Each diffuser on your account is a Home Assistant device (manufacturer EverScent, model Whole Home Diffuser) with the entities below. Values update on every [poll](how-it-works.md), 60 seconds by default. Entities marked "disabled by default" are in the entity registry; enable them in the device's entity list.

## Switches

| Entity | What it does |
| :--- | :--- |
| Power | Turns the diffuser on or off. On means the cloud reports it active. |
| Schedule HH:MM-HH:MM | One per configured schedule, named from its time window. On means the schedule is enabled. Turning it off disables it without deleting it. |

A schedule switch has these attributes: `schedule_group_id`, `days` (0 is Sunday, 6 is Saturday), `start_time`, `end_time`, `diffusing_seconds`, `pausing_seconds` and `concentration`. Use `schedule_group_id` with the [actions](actions.md). A switch becomes unavailable when its schedule is deleted.

## Sensors

| Entity | Meaning |
| :--- | :--- |
| Fragrance | Name of the installed fragrance. |
| Fragrance level | The `fragranceLevel` value the cloud reports for the installed bottle, unchanged. It may not track how much oil is left. Use Fragrance low to know when to replace the bottle. |
| Fragrance category | Category of the installed fragrance. |
| Concentration | Concentration level of the current schedule. |
| Firmware version | Firmware version. Disabled by default. |
| Wi-Fi network | Name of the Wi-Fi network the diffuser uses. Disabled by default. |
| Location | Location name set in the EverScent app. Disabled by default. |

## Binary sensors

| Entity | Device class | Meaning |
| :--- | :--- | :--- |
| Online | Connectivity | On when the cloud reports the device online. |
| Fragrance low | Problem | On when the bottle is low. |
| Battery low | Battery | On when the device reports a low battery. |
| Fan | Running | On while the fan runs. |
| Light | Light | On while the device light is on. |
| Firmware update available | Update | On when an update is available. Disabled by default. |

## Buttons

| Entity | What it does |
| :--- | :--- |
| Quick scent | Starts a one-off scent burst for the length set by Quick scent duration. |
| Acknowledge empty bottle | Acknowledges an empty-bottle alert. Disabled by default. |

## Number

| Entity | Meaning |
| :--- | :--- |
| Quick scent duration | How long the Quick scent button runs, in seconds. Range 5 to 120, default 30. It is a configuration entity. |

The cloud has no stored setting for the duration. It is sent with each quick scent request, so Home Assistant keeps the value and restores it after a restart.
