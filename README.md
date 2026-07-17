# Alert Hub

A small custom Home Assistant integration that:

- Lets you name and enable/disable a set of **Browser Mod** target devices via a Configure (options) flow — no more guessing which anonymous Browser Mod device ID is which tablet.
- Maintains a single, persistent, growing/shrinking **active alerts queue** as `sensor.alert_hub_active_alerts` (state = alert count, `alerts` attribute = full list, survives HA restarts).
- Exposes three services: `alert_hub.add_alert`, `alert_hub.clear_alert`, `alert_hub.clear_all`.
- Automatically keeps **one** Browser Mod popup (same `tag`, so it updates in place instead of stacking) in sync with each target device's own filtered slice of the queue — it grows as matching alerts are added and shrinks as they're cleared, closing itself when nothing matches.

## Install

1. In HA: HACS → the "⋮" menu (top right) → **Custom repositories** → add this repo's URL, category **Integration**.
2. Install "Alert Hub" from HACS, then restart Home Assistant.
3. Settings → Devices & Services → **Add Integration** → search "Alert Hub" → Submit (no fields needed).
4. Click **Configure** on the new Alert Hub integration card → **Add a device** → give it a friendly name and pick the corresponding Browser Mod device. Repeat for each real device you want alerts to appear on. Choose **Done** when finished.

## Filtering which alerts show on which device

Alert Hub does **not** auto-capture every `persistent_notification` in your system — that pulls in noise (HomeKit pairing codes, internal exception spam, etc.). Instead, you deliberately call `alert_hub.add_alert` from the specific automations you actually care about, optionally tagging each alert with `source_device_id`: the real HA device it relates to (e.g. the front door sensor's device, the washing machine plug's device).

When adding or editing a target device, the **"Only show alerts from these devices"** field is a device picker:

- Leave it empty → that device shows *every* alert regardless of source (a good default for your own phone).
- Pick specific devices → that target only shows alerts whose `source_device_id` matches one of the picked devices. Alerts with no source device, or a source not in the list, are hidden there (but still visible on devices with no filter, and always counted in full in `sensor.alert_hub_active_alerts`).

To change a device's filter later without removing/re-adding it: Configure → **Edit a device's alert filter** → pick the device → update its source devices (or toggle it off entirely).

## Wiring up an alert

Example: notify when the front door has been left open for 10 minutes, tagged with the door sensor's own device so it can be routed to specific screens:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.front_door
    to: "on"
    for:
      minutes: 10
actions:
  - action: alert_hub.add_alert
    data:
      title: "Security"
      message: "Front door has been open for 10 minutes"
      source_device_id: "{{ device_id('binary_sensor.front_door') }}"
```

And to clear it again once the door closes:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.front_door
    to: "off"
actions:
  - action: alert_hub.clear_alert
    data:
      alert_id: "{{ alert_id_variable }}"   # capture the id returned by add_alert, e.g. via response_variable
```

Repeat this pattern per thing you want tracked (washing machine finished, EV charging done, low battery, etc.) — each with its own trigger and its own `source_device_id`.
