from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN
from .core.entity import FluvalEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([FluvalSwitch(device, "led_on_off")])


class FluvalSwitch(FluvalEntity, SwitchEntity):
    _attr_device_class = SwitchDeviceClass.SWITCH

    def internal_update(self):
        attribute = self.device.attribute(self.attr)
        if not attribute:
            return

        self._attr_is_on = attribute.get("is_on")

        if self.hass:
            self._async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
