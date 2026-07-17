"""The Alert Hub integration.

Owns:
  - a config/options flow for naming and enabling target Browser Mod devices,
    each with an optional list of *source* HA devices it should show alerts
    for (picked via a device selector)
  - a native "active alerts" queue (sensor.alert_hub_active_alerts) that
    grows and shrinks as alerts are added/cleared
  - services (add_alert / clear_alert / clear_all) that automations call
  - the logic that keeps a single Browser Mod popup (identified by a fixed
    `tag`) in sync with each device's own filtered slice of the queue
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_ALERT_ID,
    ATTR_MESSAGE,
    ATTR_SOURCE_DEVICE_ID,
    ATTR_TITLE,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_ENABLED,
    CONF_SOURCE_DEVICES,
    DOMAIN,
    POPUP_TAG,
    SERVICE_ADD_ALERT,
    SERVICE_CLEAR_ALERT,
    SERVICE_CLEAR_ALL,
    SIGNAL_ALERTS_UPDATED,
)
from .store import AlertHubStore

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

ADD_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_SOURCE_DEVICE_ID): cv.string,
    }
)
CLEAR_ALERT_SCHEMA = vol.Schema({vol.Required(ATTR_ALERT_ID): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alert Hub from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    store = AlertHubStore(hass, entry.entry_id)
    await store.async_load()
    hass.data[DOMAIN][entry.entry_id] = store

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    def _enabled_devices() -> list[dict[str, Any]]:
        return [
            d for d in entry.options.get(CONF_DEVICES, []) if d.get(CONF_ENABLED, True)
        ]

    def _visible_alerts_for(device: dict[str, Any]) -> list[dict[str, Any]]:
        """Alerts this device should see. Empty/missing 'source_devices' =
        no filter = every alert (matches pre-filtering behavior). Otherwise
        only alerts whose source_device_id is one of the picked devices."""
        wanted = device.get(CONF_SOURCE_DEVICES) or []
        if not wanted:
            return store.alerts
        wanted_set = set(wanted)
        return [a for a in store.alerts if a.get("source_device_id") in wanted_set]

    def _render_content(alerts: list[dict[str, Any]]) -> str:
        lines = []
        for alert in alerts:
            ts = alert["created"][11:16]  # HH:MM out of the ISO timestamp
            prefix = f"**{alert['title']}:** " if alert.get("title") else ""
            lines.append(f"- `{ts}` {prefix}{alert['message']}")
        return "\n".join(lines)

    async def _sync_popup() -> None:
        """Push each device its own filtered slice of the alert queue as a
        single, updating popup (same tag = replace in place, not stack).
        A device with no matching alerts gets its popup closed instead."""
        for device in _enabled_devices():
            device_id = device[CONF_DEVICE_ID]
            visible = _visible_alerts_for(device)

            if not visible:
                await hass.services.async_call(
                    "browser_mod",
                    "close_popup",
                    {"tag": POPUP_TAG, "browser_id": [device_id]},
                    blocking=True,
                )
                continue

            await hass.services.async_call(
                "browser_mod",
                "popup",
                {
                    "browser_id": [device_id],
                    "tag": POPUP_TAG,
                    "title": f"\U0001f514 Active Alerts ({len(visible)})",
                    "content": {
                        "type": "markdown",
                        "content": _render_content(visible),
                    },
                    "initial_style": "normal",
                    "dismissable": True,
                    "right_button": "Clear all",
                    "right_button_action": {"action": f"{DOMAIN}.{SERVICE_CLEAR_ALL}"},
                },
                blocking=True,
            )

    async def _async_refresh() -> None:
        async_dispatcher_send(hass, SIGNAL_ALERTS_UPDATED.format(entry_id=entry.entry_id))
        await _sync_popup()

    async def _handle_add_alert(call: ServiceCall) -> None:
        await store.async_add(
            call.data[ATTR_MESSAGE],
            call.data.get(ATTR_TITLE),
            call.data.get(ATTR_SOURCE_DEVICE_ID),
        )
        await _async_refresh()

    async def _handle_clear_alert(call: ServiceCall) -> None:
        await store.async_clear(call.data[ATTR_ALERT_ID])
        await _async_refresh()

    async def _handle_clear_all(call: ServiceCall) -> None:
        await store.async_clear_all()
        await _async_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_ALERT, _handle_add_alert, schema=ADD_ALERT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_ALERT, _handle_clear_alert, schema=CLEAR_ALERT_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_ALL, _handle_clear_all)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Options (device list) changed - nothing to reload, services read
    entry.options live on every call."""
    return


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        for service in (SERVICE_ADD_ALERT, SERVICE_CLEAR_ALERT, SERVICE_CLEAR_ALL):
            hass.services.async_remove(DOMAIN, service)
    return unloaded
