"""Sensor platform for Petkit BLE integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from datetime import datetime
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
    """Set up Petkit BLE sensors."""
    coordinator: PetkitBLECoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        PetkitBatteryLevelSensor(coordinator),
        PetkitFilterPercentageSensor(coordinator),
        PetkitFilterTimeLeftSensor(coordinator),
        PetkitPumpRuntimeSensor(coordinator),
        PetkitPumpRuntimeTodaySensor(coordinator),
        PetkitPurifiedWaterSensor(coordinator),
        PetkitPurifiedWaterTodaySensor(coordinator),
        PetkitEnergyConsumedSensor(coordinator),
        PetkitRSSISensor(coordinator),
        PetkitVoltageSensor(coordinator),
        PetkitConnectionStatusSensor(coordinator),
        PetkitConnectionAttemptsSensor(coordinator),
        PetkitLastSeenSensor(coordinator),
    ]
    
    async_add_entities(entities)

class PetkitSensorBase(CoordinatorEntity[PetkitBLECoordinator], SensorEntity):
    """Base class for Petkit sensors."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        # Device info will be provided by the dynamic property
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info dynamically."""
        # Use address as identifier if serial is not initialized yet
        device_id = self.coordinator.device.serial if self.coordinator.device.serial != "Uninitialized" else self.coordinator.address
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": self.coordinator.device.name_readable,
            "manufacturer": "Petkit",
            "model": self.coordinator.device.product_name,
            "sw_version": str(self.coordinator.device.firmware),
        }
    
    @property
    def name(self) -> str:
        """Return dynamic entity name."""
        # Override static _attr_name with dynamic name based on current device state
        device_name = self.coordinator.device.name_readable if self.coordinator.device.name_readable != "Uninitialized" else "Petkit Device"
        # Return the sensor-specific name if defined, otherwise fallback
        return getattr(self, '_sensor_name_template', device_name).format(device_name=device_name)
    
    def _get_device_id(self) -> str:
        """Get device ID for unique_id generation."""
        if self.coordinator.device.serial != "Uninitialized":
            return self.coordinator.device.serial
        return self.coordinator.address.replace(":", "")

class PetkitBatteryLevelSensor(PetkitSensorBase):
    """Battery level sensor."""
    
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_battery"
        self._sensor_name_template = "{device_name} Battery"
    
    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        return self.coordinator.current_data.get("status", {}).get("battery")

class PetkitFilterPercentageSensor(PetkitSensorBase):
    """Filter percentage sensor."""
    
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:air-filter"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the filter percentage sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_filter_percentage"
        self._attr_name = f"{coordinator.device.name_readable} Filter"
    
    @property
    def native_value(self) -> int | None:
        """Return the filter percentage."""
        return self.coordinator.current_data.get("status", {}).get("filter_percentage")

class PetkitFilterTimeLeftSensor(PetkitSensorBase):
    """Filter time left sensor."""
    
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:clock-outline"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the filter time left sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_filter_time_left"
        self._attr_name = f"{coordinator.device.name_readable} Filter Time Left"
    
    @property
    def native_value(self) -> int | None:
        """Return the filter time left in days."""
        return self.coordinator.current_data.get("status", {}).get("filter_time_left")

class PetkitPumpRuntimeSensor(PetkitSensorBase):
    """Pump runtime sensor."""
    
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:pump"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the pump runtime sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_pump_runtime"
        self._attr_name = f"{coordinator.device.name_readable} Pump Runtime"
    
    @property
    def native_value(self) -> str | None:
        """Return the pump runtime."""
        return self.coordinator.current_data.get("status", {}).get("pump_runtime_readable")

class PetkitPumpRuntimeTodaySensor(PetkitSensorBase):
    """Pump runtime today sensor."""
    
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:pump"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the pump runtime today sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_pump_runtime_today"
        self._attr_name = f"{coordinator.device.name_readable} Pump Runtime Today"
    
    @property
    def native_value(self) -> str | None:
        """Return the pump runtime today."""
        return self.coordinator.current_data.get("status", {}).get("pump_runtime_today_readable")

class PetkitPurifiedWaterSensor(PetkitSensorBase):
    """Purified water sensor."""
    
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:water"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the purified water sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_purified_water"
        self._attr_name = f"{coordinator.device.name_readable} Purified Water"
    
    @property
    def native_value(self) -> float | None:
        """Return the total purified water."""
        return self.coordinator.current_data.get("status", {}).get("purified_water")

class PetkitPurifiedWaterTodaySensor(PetkitSensorBase):
    """Purified water today sensor."""
    
    _attr_native_unit_of_measurement = UnitOfVolume.LITERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:water"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the purified water today sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_purified_water_today"
        self._attr_name = f"{coordinator.device.name_readable} Purified Water Today"
    
    @property
    def native_value(self) -> float | None:
        """Return today's purified water."""
        return self.coordinator.current_data.get("status", {}).get("purified_water_today")

class PetkitEnergyConsumedSensor(PetkitSensorBase):
    """Energy consumed sensor."""
    
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the energy consumed sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_energy_consumed"
        self._attr_name = f"{coordinator.device.name_readable} Energy Consumed"
    
    @property
    def native_value(self) -> float | None:
        """Return the energy consumed."""
        return self.coordinator.current_data.get("status", {}).get("energy_consumed")

class PetkitRSSISensor(PetkitSensorBase):
    """RSSI sensor."""
    
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the RSSI sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_rssi"
        self._attr_name = f"{coordinator.device.name_readable} Signal Strength"
    
    @property
    def native_value(self) -> int | None:
        """Return the RSSI value."""
        return self.coordinator.current_data.get("status", {}).get("rssi")

class PetkitVoltageSensor(PetkitSensorBase):
    """Voltage sensor."""
    
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the voltage sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_voltage"
        self._attr_name = f"{coordinator.device.name_readable} Voltage"
    
    @property
    def native_value(self) -> float | None:
        """Return the voltage."""
        return self.coordinator.current_data.get("status", {}).get("voltage")

class PetkitConnectionStatusSensor(PetkitSensorBase):
    """Connection status sensor."""
    
    _attr_icon = "mdi:bluetooth-connect"
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the connection status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_connection_status"
        self._attr_name = f"{coordinator.device.name_readable} Connection Status"
    
    @property
    def native_value(self) -> str | None:
        """Return the connection status."""
        return self.coordinator.current_data.get("status", {}).get("connection_status", "unknown")

class PetkitConnectionAttemptsSensor(PetkitSensorBase):
    """Connection attempts sensor."""
    
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the connection attempts sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_connection_attempts"
        self._attr_name = f"{coordinator.device.name_readable} Connection Attempts"
    
    @property
    def native_value(self) -> int | None:
        """Return the number of connection attempts."""
        return self.coordinator.current_data.get("status", {}).get("connection_attempts", 0)

class PetkitLastSeenSensor(PetkitSensorBase):
    """Last seen sensor."""
    
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the last seen sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._get_device_id()}_last_seen"
        self._attr_name = f"{coordinator.device.name_readable} Last Seen"
    
    @property
    def native_value(self) -> datetime | None:
        """Return the last seen timestamp."""
        last_seen = self.coordinator.current_data.get("status", {}).get("last_seen")
        if last_seen:
            # Handle both timestamp (float) and ISO string formats for backward compatibility
            if isinstance(last_seen, str):
                try:
                    from datetime import datetime as dt
                    # Parse ISO format string to datetime
                    return dt.fromisoformat(last_seen.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    return None
            else:
                # Legacy numeric timestamp format
                return datetime.fromtimestamp(last_seen)
        return None