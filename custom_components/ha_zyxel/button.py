"""Support for Zyxel device buttons."""
from __future__ import annotations

import logging
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .entity import ZyxelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Zyxel buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    router = hass.data[DOMAIN][entry.entry_id]["router"]
    async_add_entities([ZyxelRebootButton(coordinator, entry, router)])


class ZyxelRebootButton(ZyxelEntity, ButtonEntity):
    """Representation of a Zyxel reboot button."""

    def __init__(self, coordinator, entry: ConfigEntry, router) -> None:
        """Initialize the button."""
        super().__init__(coordinator, entry)
        self._router = router
        self._attr_unique_id = f"{entry.entry_id}_reboot"
        self._attr_name = "Reboot Device"
        self._attr_device_class = ButtonDeviceClass.RESTART
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self) -> DeviceInfo:
        """Haal modelinformatie uit de coordinator data."""
        data = self.coordinator.data
        model_name = "Zyxel Device"
        
        if data and "DeviceInfo" in data:
            model_name = data["DeviceInfo"].get("ModelName", "Zyxel Device")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Zyxel ({self._entry.data['host']})",
            manufacturer="Zyxel",
            model=model_name,
        )


    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.warning("Reboot command triggered for Zyxel device at %s", self._attr_unique_id)
        try:
            await self.hass.async_add_executor_job(self._router.reboot)
        except Exception as err:
            _LOGGER.error("Failed to send reboot command: %s", err)
            raise # To show error in UI