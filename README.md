# Alert Hub

A small custom Home Assistant integration that:

- Lets you name and enable/disable a set of **Browser Mod** target devices via a Configure (options) flow — no more guessing which anonymous Browser Mod device ID is which tablet.
- Maintains a single, persistent, growing/shrinking **active alerts queue** as `sensor.alert_hub_active_alerts` (state = alert count, `alerts` attribute = full list, survives HA restarts).
- Exposes three services: `alert_hub.add_alert`, `alert_hub.clear_alert`, `alert_hub.clear_all`.
- Automatically keeps **one** Browser Mod popup (same `tag`, so it updates in place instead of stacking) in sync with the queue on every enabled device — the popup grows as alerts are added and shrinks as they're cleared, and closes itself when the queue is empty.

## Install

1. In HA: HACS → the "⋮" menu (top right) → **Custom repositories** → add this repo's URL, category **Integration**.
2. Install "Alert Hub" from HACS, then restart Home Assistant.
3. Settings → Devices & Services → **Add Integration** → search "Alert Hub" → Submit (no fields needed).
4. Click **Configure** on the new Alert Hub integration card → **Add a device** → give it a friendly name and pick the corresponding Browser Mod device. Repeat for each real device you want alerts to appear on. Choose **Done** when finished.

## Wiring up notifications

Point your existing "new persistent notification" automation at this integration instead of a plain helper:

```yaml
triggers:
  - trigger: persistent_notification
    update_type: ["added"]
actions:
  - action: alert_hub.add_alert
    data:
      title: "{{ trigger.notification.title }}"
      message: "{{ trigger.notification.message }}"
```

And to shrink the queue when a notification is dismissed elsewhere:

```yaml
triggers:
  - trigger: persistent_notification
    update_type: ["removed"]
actions:
  - action: alert_hub.clear_alert
    data:
      alert_id: "{{ trigger.notification.notification_id }}"
```

(Home Assistant will keep automation-level trigger and action logic; Alert Hub itself only owns the queue, the device list, and the popup sync.)
