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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
    ]
    
    async_add_entities(entities)

class PetkitSensorBase(CoordinatorEntity[PetkitBLECoordinator], SensorEntity):
    """Base class for Petkit sensors."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device.serial)},
            "name": coordinator.device.name_readable,
            "manufacturer": "Petkit",
            "model": coordinator.device.product_name,
            "sw_version": str(coordinator.device.firmware),
        }

class PetkitBatteryLevelSensor(PetkitSensorBase):
    """Battery level sensor."""
    
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.serial}_battery"
        self._attr_name = f"{coordinator.device.name_readable} Battery"
    
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
        self._attr_unique_id = f"{coordinator.device.serial}_filter_percentage"
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
        self._attr_unique_id = f"{coordinator.device.serial}_filter_time_left"
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
        self._attr_unique_id = f"{coordinator.device.serial}_pump_runtime"
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
        self._attr_unique_id = f"{coordinator.device.serial}_pump_runtime_today"
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
        self._attr_unique_id = f"{coordinator.device.serial}_purified_water"
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
        self._attr_unique_id = f"{coordinator.device.serial}_purified_water_today"
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
        self._attr_unique_id = f"{coordinator.device.serial}_energy_consumed"
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
        self._attr_unique_id = f"{coordinator.device.serial}_rssi"
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
        self._attr_unique_id = f"{coordinator.device.serial}_voltage"
        self._attr_name = f"{coordinator.device.name_readable} Voltage"
    
    @property
    def native_value(self) -> float | None:
        """Return the voltage."""
        return self.coordinator.current_data.get("status", {}).get("voltage")