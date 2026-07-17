"""Persistent alert queue for Alert Hub.

Holds the growing/shrinking list of active alerts, backed by Home
Assistant's Store helper so the queue survives restarts.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


class AlertHubStore:
    """In-memory + persisted list of active alerts for one config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._store: Store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        self.alerts: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        """Load any previously persisted alerts."""
        data = await self._store.async_load()
        if data and isinstance(data.get("alerts"), list):
            self.alerts = data["alerts"]

    async def _async_save(self) -> None:
        await self._store.async_save({"alerts": self.alerts})

    async def async_add(
        self,
        message: str,
        title: str | None = None,
        source_device_id: str | None = None,
    ) -> str:
        """Add a new alert to the queue. Returns its id."""
        alert_id = uuid.uuid4().hex[:8]
        self.alerts.append(
            {
                "id": alert_id,
                "title": title,
                "message": message,
                "source_device_id": source_device_id,
                "created": datetime.now(timezone.utc).isoformat(),
            }
        )
        await self._async_save()
        return alert_id

    async def async_clear(self, alert_id: str) -> bool:
        """Remove a single alert by id. Returns True if something was removed."""
        before = len(self.alerts)
        self.alerts = [a for a in self.alerts if a["id"] != alert_id]
        if len(self.alerts) != before:
            await self._async_save()
            return True
        return False

    async def async_clear_all(self) -> None:
        """Empty the queue."""
        self.alerts = []
        await self._async_save()
