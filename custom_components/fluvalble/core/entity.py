from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import DOMAIN
from .device import Device


class FluvalEntity(Entity):
    _attr_should_poll = False

    def __init__(self, device: Device, attr: str):
        self.device = device
        self.attr = attr

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            identifiers={(DOMAIN, device.mac)},
            manufacturer="Fluval",
            model="todo",
            name=device.name or "Fluval",
        )
        self._attr_name = device.name + " " + attr.replace("_", " ").title()
        self._attr_unique_id = device.mac.replace(":", "") + "_" + attr

        self.entity_id = DOMAIN + "." + self._attr_unique_id

        self.internal_update()

        device.register_update(attr, self.internal_update)

    def internal_update(self):
        pass
