# Actions

Both actions manage schedules. Find `device_id` and `schedule_group_id` in the [schedule switch attributes](entities.md).

## everscent.set_schedule

Creates a schedule. Include `schedule_group_id` to update an existing one instead. The schedule is saved as enabled.

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `device_id` | Yes | EverScent device id. |
| `schedule_group_id` | No | Update this schedule. Omit to create one. |
| `days` | Yes | Days it runs, 0 (Sunday) to 6 (Saturday). |
| `start_time` | Yes | Start of the window, `HH:MM`, 24 hour. |
| `end_time` | Yes | End of the window, `HH:MM`, 24 hour. |
| `standard_setting_id` | No | A built-in intensity preset. |
| `diffusing_seconds` | No | Custom setting: seconds of misting per cycle. |
| `pausing_seconds` | No | Custom setting: seconds paused between mists. |
| `concentration` | No | Custom setting: level 1 to 3. |

Give either `standard_setting_id`, or all of `diffusing_seconds`, `pausing_seconds` and `concentration`. Anything else is refused.

With a preset:

```yaml
action: everscent.set_schedule
data:
  device_id: 1864
  days: [1, 2, 3, 4, 5]
  start_time: "07:00"
  end_time: "22:00"
  standard_setting_id: 3
```

With a custom setting:

```yaml
action: everscent.set_schedule
data:
  device_id: 1864
  days: [0, 6]
  start_time: "09:00"
  end_time: "20:00"
  diffusing_seconds: 20
  pausing_seconds: 90
  concentration: 3
```

## everscent.delete_schedule

Deletes a schedule by its group id.

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `schedule_group_id` | Yes | The schedule to delete. |

```yaml
action: everscent.delete_schedule
data:
  schedule_group_id: "cfd1535c-1604-43ff-a9ed-7eb3a188024a"
```

After either action the integration refreshes its data.

The actions are registered when the integration loads and stay available while Home Assistant runs. With no EverScent account set up they fail with "No EverScent account is configured".
