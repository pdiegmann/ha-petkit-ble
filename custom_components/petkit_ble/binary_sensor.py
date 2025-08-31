"""Binary sensor platform for Petkit BLE integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import PetkitBLECoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Petkit BLE binary sensors."""
    coordinator: PetkitBLECoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        PetkitFilterProblemSensor(coordinator),
        PetkitWaterMissingSensor(coordinator),
        PetkitBreakdownSensor(coordinator),
        PetkitRunningSensor(coordinator),
    ]
    
    async_add_entities(entities)

class PetkitBinarySensorBase(CoordinatorEntity[PetkitBLECoordinator], BinarySensorEntity):
    """Base class for Petkit binary sensors."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        # Use MAC address as fallback if serial not available
        # Device info will be provided by the dynamic property
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info dynamically."""
        device_id = self.coordinator.device.serial if self.coordinator.device.serial != "Uninitialized" else self.coordinator.address
        device_name = self.coordinator.device.name_readable if self.coordinator.device.name_readable != "Uninitialized" else "Water Fountain"
        
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Petkit",
            "model": self.coordinator.device.product_name or "Water Fountain",
            "sw_version": str(self.coordinator.device.firmware) if self.coordinator.device.firmware else "Unknown",
        }

class PetkitFilterProblemSensor(PetkitBinarySensorBase):
    """Filter problem binary sensor."""
    
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the filter problem sensor."""
        super().__init__(coordinator)
        device_id = coordinator.device.serial if coordinator.device.serial != "Uninitialized" else coordinator.address.replace(":", "")
        self._attr_unique_id = f"{device_id}_filter_problem"
        self._attr_name = "Filter Problem"
        self._attr_icon = "mdi:air-filter"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if there's a filter problem."""
        warning = self.coordinator.current_data.get("status", {}).get("warning_filter")
        return bool(warning) if warning is not None else None

class PetkitWaterMissingSensor(PetkitBinarySensorBase):
    """Water missing binary sensor."""
    
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the water missing sensor."""
        super().__init__(coordinator)
        device_id = coordinator.device.serial if coordinator.device.serial != "Uninitialized" else coordinator.address.replace(":", "")
        self._attr_unique_id = f"{device_id}_water_missing"
        self._attr_name = "Water Missing"
        self._attr_icon = "mdi:water-alert"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if water is missing."""
        warning = self.coordinator.current_data.get("status", {}).get("warning_water_missing")
        return bool(warning) if warning is not None else None

class PetkitBreakdownSensor(PetkitBinarySensorBase):
    """Breakdown binary sensor."""
    
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the breakdown sensor."""
        super().__init__(coordinator)
        device_id = coordinator.device.serial if coordinator.device.serial != "Uninitialized" else coordinator.address.replace(":", "")
        self._attr_unique_id = f"{device_id}_breakdown"
        self._attr_name = "Breakdown"
        self._attr_icon = "mdi:alert-circle"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if there's a breakdown."""
        warning = self.coordinator.current_data.get("status", {}).get("warning_breakdown")
        return bool(warning) if warning is not None else None

class PetkitRunningSensor(PetkitBinarySensorBase):
    """Running status binary sensor."""
    
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the running sensor."""
        super().__init__(coordinator)
        device_id = coordinator.device.serial if coordinator.device.serial != "Uninitialized" else coordinator.address.replace(":", "")
        self._attr_unique_id = f"{device_id}_running"
        self._attr_name = "Running"
        self._attr_icon = "mdi:play-circle"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if the fountain is running."""
        running_status = self.coordinator.current_data.get("status", {}).get("running_status")
        return bool(running_status) if running_status is not None else None