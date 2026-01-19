"""Support for Zyxel device sensors."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import (
    DeviceInfo,
    EntityCategory,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from custom_components.ha_zyxel.const import DOMAIN

from .entity import ZyxelEntity

_LOGGER = logging.getLogger(__name__)

# Define some known sensor types for proper configuration
KNOWN_SENSORS = {
    "INTF_RSSI": {
        "name": "Cellular RSSI",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_PhyCell_ID": {
        "name": "Physical Cell ID",
        "unit": None,
        "icon": "mdi:antenna",
        "device_class": None,
        "state_class": None,
    },
    "INTF_RSRP": {
        "name": "Cellular Reference Signal Received Power",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_RSRQ": {
        "name": "Cellular Reference Signal Received Quality",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_SINR": {
        "name": "Cellular Signal-to-Noise Ratio",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_MCS": {
        "name": "Cellular Modulation and Coding Scheme",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_CQI": {
        "name": "Cellular Channel Quality Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_RI": {
        "name": "Cellular Rank Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_PMI": {
        "name": "Cellular Precoding Matrix Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "NSA_PhyCellID": {
        "name": "NSA Physical Cell ID",
        "unit": None,
        "icon": "mdi:antenna",
        "device_class": None,
        "state_class": None,
    },
    "NSA_RSRP": {
        "name": "NSA Reference Signal Received Power",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_RSRQ": {
        "name": "NSA Reference Signal Received Quality",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_RSSI": {
        "name": "NSA Reference Signal Strength Indicator",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_SINR": {
        "name": "NSA Signal-to-Noise Ratio",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "X_ZYXEL_TEMPERATURE_AMBIENT": {
        "name": "Ambient Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "X_ZYXEL_TEMPERATURE_SDX": {
        "name": "SDX Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "X_ZYXEL_TEMPERATURE_CPU0": {
        "name": "CPU Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "BytesSent": {
        "name": "Bytes Sent",
        "unit": "B",
        "icon": "mdi:numeric-10-box",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "BytesReceived": {
        "name": "Bytes Received",
        "unit": "B",
        "icon": "mdi:numeric-10-box",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "Total": {
        "name": "Total memory",
        "unit": "B",
        "icon": "mdi:memory",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "entity_registry_enabled_default": False
    },
    "Free": {
        "name": "Free memory",
        "unit": "B",
        "icon": "mdi:memory",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "entity_registry_enabled_default": False
    },
    "CPUUsage": {
        "name": "CPU Usage",
        "unit": "%",
        "icon": "mdi:gauge",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "entity_registry_enabled_default": False        
    },
}


def _flatten_dict(d: dict, parent_key: str = "") -> dict:
    """Flatten a nested dictionary with dot notation for keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _is_value_scalar(value: Any) -> bool:
    """
    Check if a value is a scalar:
    - Numeric (int, float)
    - Boolean
    - String (must contains non-whitespace characters)
    """
    if isinstance(value, (int, float, bool)) or value is None:
        return True
    
    if isinstance(value, str):
        return len(value.strip()) > 0

    return False


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Zyxel sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    if not coordinator.data:
        return

    sensors = []

    # Process all keys in the JSON and create sensors for them
    # We'll use a flat structure for simplicity
    for key, value in _flatten_dict(coordinator.data).items():
        # Skip non-scalar values
        if not _is_value_scalar(value):
            continue
        
        # Skip LAN_client as it's handled by the device_tracker
        if key.startswith("LAN_client"):
            continue

        # Check if this is a known sensor type
        base_key = key.split(".")[-1]

        if base_key == "UpTime":
            continue  # Skip UpTime as it's handled by a dedicated sensor with unknown as attributes
        
        if base_key in KNOWN_SENSORS:
            sensors.append(ConfiguredZyxelSensor(coordinator, entry, key, KNOWN_SENSORS[base_key]))
        
    sensors.append(ZyxelDiagnosticsSensor(coordinator, entry))
    
    async_add_entities(sensors)

class AbstractZyxelSensor(ZyxelEntity, SensorEntity):
    """Base class for Zyxel device sensors."""

    def __init__(self, coordinator, entry: ConfigEntry, key: str):
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_has_entity_name = True


    @property
    def device_info(self) -> DeviceInfo:
        """Connect to device dynamically."""
        # Try to get the model from the data, otherwise fallback to Zyxel Device
        data = self.coordinator.data
        model_name = "Zyxel Router"
        
        if data and "DeviceInfo" in data:
            model_name = data["DeviceInfo"].get("ModelName", "Zyxel Device")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Zyxel ({self._entry.data['host']})",
            manufacturer="Zyxel",
            model=model_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        # Check if the key exists in the data
        try:
            self._get_value_from_path()
            return True
        except (KeyError, AttributeError):
            return False

    def _get_value_from_path(self) -> Any:
        """Get a value from nested dictionaries using the flattened key."""
        data = self.coordinator.data
        if not data:
            return None
            
        keys = self._key.split(".")
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value


class ConfiguredZyxelSensor(AbstractZyxelSensor):
    """Representation of a configured Zyxel sensor."""

    def __init__(self, coordinator, entry: ConfigEntry, key: str, config: dict):
        """Initialize the sensor."""
        super().__init__(coordinator, entry, key)
        self._config = config
        self._attr_name = f"Zyxel {config['name']}"
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_icon = config.get("icon")
        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")        
        self._attr_entity_category = config.get("entity_category")
        self._attr_entity_registry_enabled_default = config.get("entity_registry_enabled_default", True)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        try:
            return self._get_value_from_path()
        except (KeyError, AttributeError, TypeError):
            return None

class ZyxelDiagnosticsSensor(ZyxelEntity, SensorEntity):
    """Sensor with all unknown data as attributes."""

    _attr_name = "Router Status"
    _attr_icon = "mdi:information-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_uptime"
        self._last_uptime = 0
        self._last_reset_time = None

    @property
    def native_value(self) -> str:
        """Determine status based on uptime trend."""
        try:
            current_uptime = int(float(self.coordinator.data.get("DeviceInfo", {}).get("UpTime", 0)))
        except (ValueError, TypeError):
            return "Unknown"

        # Determine status
        if self._last_uptime == 0:
            # Reboot of HA, only if router was reset less than 120 seconds ago we consider this a reboot
            if current_uptime < 120:
                status = "Reset"
            else:
                status = "Up"
        elif current_uptime < self._last_uptime:
            # Current uptime lower than last uptime this is a reboot while HA was running
            status = "Reset"
        else:
            # Normal operation
            status = "Up"

        if status == "Reset":
            # Calculate the reset time: Now - Uptime
            self._last_reset_time = dt_util.utcnow() - timedelta(seconds=current_uptime)
        
        # Store new uptime for next check
        self._last_uptime = current_uptime
        return status

    @property
    def extra_state_attributes(self):
        """Store all flattened data as attributes, except the known sensors."""
        attrs = {}
        flattened_data = _flatten_dict(self.coordinator.data)
        
        # Add uptime so we can still see it as an attribute
        attrs["uptime_seconds"] = self._last_uptime

        # Add last reset time if available        
        if self._last_reset_time:
            attrs["last_reset"] = self._last_reset_time.isoformat()
        
        for key, value in flattened_data.items():
            if not _is_value_scalar(value):
                continue

            base_key = key.split(".")[-1]
            # Only when NOT a known sensor (to avoid duplicate data)
            if base_key not in KNOWN_SENSORS and base_key != "UpTime":
                # Replace dots with underscores for clean attribute names
                attr_name = key.replace(".", "_")
                attrs[attr_name] = value
                
        return attrs