"""The Fluval Aquarium LED integration."""
from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .core import DOMAIN
from .core.device import Device

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fluval Aquarium LED from a config entry."""
    devices = hass.data.setdefault(DOMAIN, {})

    @callback
    def update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        logging.debug(entry.entry_id)
        logging.debug(entry.title)
        logging.debug(service_info.device)
        logging.debug(service_info.advertisement)
        if device := devices.get(entry.entry_id):
            device.update_ble(service_info)
            return

        devices[entry.entry_id] = Device(
            entry.title, service_info.device, service_info.advertisement
        )

        hass.create_task(
            hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        )

    # https://developers.home-assistant.io/docs/core/bluetooth/api/
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            update_ble,
            {"address": entry.data["mac"], "manufacturer_id": 171, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
