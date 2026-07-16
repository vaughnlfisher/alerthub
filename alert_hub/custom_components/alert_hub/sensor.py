"""The Alert Hub active-alerts sensor."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICES, CONF_ENABLED, CONF_LABEL, DOMAIN, SIGNAL_ALERTS_UPDATED
from .store import AlertHubStore


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store: AlertHubStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlertHubSensor(entry, store)])


class AlertHubSensor(SensorEntity):
    """State = number of active alerts. Attributes carry the full queue
    (grows/shrinks as alerts are added/cleared) plus the currently
    enabled target devices."""

    _attr_has_entity_name = True
    _attr_name = "Active Alerts"
    _attr_icon = "mdi:bell-alert"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, store: AlertHubStore) -> None:
        self._entry = entry
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_active_alerts"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Alert Hub",
            manufacturer="Custom",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_ALERTS_UPDATED.format(entry_id=self._entry.entry_id),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        return len(self._store.alerts)

    @property
    def extra_state_attributes(self) -> dict:
        targets = [
            d[CONF_LABEL]
            for d in self._entry.options.get(CONF_DEVICES, [])
            if d.get(CONF_ENABLED, True)
        ]
        return {
            "alerts": self._store.alerts,
            "targets": targets,
        }
