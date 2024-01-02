"""The Fluval Aquarium LED integration."""
from __future__ import annotations

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_MAC

from .core import DOMAIN
from .core.device import Device

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.BINARY_SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fluval Aquarium LED from a config entry."""
    devices = hass.data.setdefault(DOMAIN, {})
    logging.debug("Entry ID: " + entry.entry_id)
    logging.debug("Entry Title: " + entry.title)
    logging.debug("Entry Conf_mac: " + str(entry.data[CONF_MAC]))

    @callback
    def update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        logging.info("XXX Service Device: " + str(service_info.device))
        logging.info("XXX Service Advertisement: " + str(service_info.advertisement))
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
            {"address": entry.data[CONF_MAC]},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
