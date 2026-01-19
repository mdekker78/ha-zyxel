from __future__ import annotations

from homeassistant.components.device_tracker import (
    SourceType,
    ScannerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ZyxelEntity

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup the Zyxel device trackers."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # We track which trackers we already have created
    tracked_devices = set()
    
    def add_new_devices():
        """Check voor new devices in the lanhosts list."""
        new_entities = []
        hosts = coordinator.data.get("lanhosts", [])
        
        for host in hosts:
            mac = host.get("PhysAddress")
            if mac and mac not in tracked_devices:
                new_entities.append(ZyxelDeviceTracker(coordinator, entry, mac))
                tracked_devices.add(mac)
        
        if new_entities:
            async_add_entities(new_entities)

    # Add the current devices
    add_new_devices()

class ZyxelDeviceTracker(ZyxelEntity, ScannerEntity):
    """Represents a device on the Zyxel network."""
    
    _attr_entity_category = None

    def __init__(self, coordinator, entry, mac):
        """Initialise the tracker."""
        super().__init__(coordinator, entry)
        self._mac = mac
        self._attr_unique_id = f"{entry.entry_id}_{mac}"
        self._attr_name = self.name

    @property
    def _host_info(self):
        """Find the specific host data in the coordinator data."""        
        hosts = self.coordinator.data.get("lanhosts", [])
        return next((h for h in hosts if h.get("PhysAddress") == self._mac), {})

    @property
    def is_connected(self) -> bool:
        """Return True when the device is active."""
        return self._host_info.get("Active") is True
        
    @property
    def icon(self) -> str:
        """Dynamisch icoon op basis van verbinding en status."""
        info = self._host_info
        conn_type = info.get("X_ZYXEL_ConnectionType", "").lower()
        active = self.is_connected

        if not active:
            return "mdi:wifi-off" if "wi-fi" in conn_type else "mdi:lan-disconnect"

        if "wi-fi" in conn_type:
            return "mdi:wifi"
        
        return "mdi:lan-connect"

    @property
    def source_type(self) -> SourceType:
        """Zyxel is a router, so we use the Router source."""
        return SourceType.ROUTER

    @property
    def name(self) -> str:
        """Determine the name of the device."""
        info = self._host_info
        # Use HostName, Alias or IP as name
        name = info.get("HostName") or info.get("Alias") or info.get("IPAddress")
        return name.strip('"') if name else f"Unknown ({self._mac})"

    @property
    def ip_address(self) -> str | None:
        """IP adres of the device."""
        return self._host_info.get("IPAddress")

    @property
    def mac_address(self) -> str:
        """MAC adres of the device."""
        return self._mac

    @property
    def extra_state_attributes(self):
        """Add extra info like signal strength and connection type."""
        info = self._host_info
        return {
            "connection_type": info.get("X_ZYXEL_ConnectionType"),
            "rssi": info.get("X_ZYXEL_RSSI"),
            "signal_strength": info.get("X_ZYXEL_SignalStrength"),
            "band": info.get("SupportedFrequencyBands"),
            "interface": info.get("Layer1Interface"),
        }