"""Constants for the Alert Hub integration."""

DOMAIN = "alert_hub"

# Options keys
CONF_DEVICES = "devices"
CONF_DEVICE_ID = "device_id"
CONF_LABEL = "label"
CONF_ENABLED = "enabled"
# Optional list of HA device_ids this target device should show alerts
# for (picked via a device selector). Empty/missing = no filter = show
# every alert (backwards compatible).
CONF_SOURCE_DEVICES = "source_devices"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "alert_hub_alerts"

# Signal dispatched when the alert list changes, so the sensor entity
# can refresh without polling.
SIGNAL_ALERTS_UPDATED = "alert_hub_alerts_updated_{entry_id}"

# Services
SERVICE_ADD_ALERT = "add_alert"
SERVICE_CLEAR_ALERT = "clear_alert"
SERVICE_CLEAR_ALL = "clear_all"

ATTR_MESSAGE = "message"
ATTR_TITLE = "title"
ATTR_ALERT_ID = "alert_id"
# Which real HA device this alert originated from (e.g. the front door
# sensor's device, the washing machine plug's device). Optional - alerts
# with no source_device_id are only visible to devices with no filter.
ATTR_SOURCE_DEVICE_ID = "source_device_id"

# Browser Mod popup
POPUP_TAG = "alert_hub_stack"
