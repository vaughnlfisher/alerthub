"""Config and options flow for Alert Hub."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_DEVICE_ID, CONF_DEVICES, CONF_ENABLED, CONF_LABEL, DOMAIN


class AlertHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial (single-instance) setup of Alert Hub."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Single-instance setup - no input needed, devices are added afterwards
        via the Configure/Options flow."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Alert Hub", data={}, options={CONF_DEVICES: []})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AlertHubOptionsFlow:
        return AlertHubOptionsFlow(config_entry)


class AlertHubOptionsFlow(config_entries.OptionsFlow):
    """Manage the list of target (Browser Mod) devices."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._devices: list[dict[str, Any]] = list(
            config_entry.options.get(CONF_DEVICES, [])
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_device", "remove_device", "finish"],
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._devices.append(
                {
                    CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                    CONF_LABEL: user_input[CONF_LABEL],
                    CONF_ENABLED: True,
                }
            )
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_LABEL): selector.TextSelector(),
                vol.Required(CONF_DEVICE_ID): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="browser_mod")
                ),
            }
        )
        return self.async_show_form(
            step_id="add_device", data_schema=schema, errors=errors
        )

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if not self._devices:
            return await self.async_step_init()

        if user_input is not None:
            to_remove = set(user_input.get("remove", []))
            self._devices = [
                d for d in self._devices if d[CONF_LABEL] not in to_remove
            ]
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required("remove"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[d[CONF_LABEL] for d in self._devices],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="remove_device", data_schema=schema)

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return self.async_create_entry(title="", data={CONF_DEVICES: self._devices})
