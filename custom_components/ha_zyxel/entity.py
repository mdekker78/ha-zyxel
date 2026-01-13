from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

class ZyxelEntity(CoordinatorEntity):
    """Shared class for all Zyxel entities."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        device_info_data = self.coordinator.data.get("DeviceInfo", {})
        model = device_info_data.get("ModelName", "Zyxel Device")
        firmware = device_info_data.get("SoftwareVersion")
        host = self._entry.data.get("host")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Zyxel {model}",
            manufacturer="Zyxel",
            model=model,
            sw_version=firmware,
            configuration_url=f"{host}" if host else None,
        )