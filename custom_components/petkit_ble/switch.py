"""Switch platform for Petkit BLE integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MODE_NORMAL, MODE_SMART, POWER_OFF, POWER_ON
from .coordinator import PetkitBLECoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Petkit BLE switches."""
    coordinator: PetkitBLECoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        PetkitPowerSwitch(coordinator),
        PetkitSmartModeSwitch(coordinator),
    ]
    
    async_add_entities(entities)

class PetkitSwitchBase(CoordinatorEntity[PetkitBLECoordinator], SwitchEntity):
    """Base class for Petkit switches."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        # Device info will be provided by the dynamic property
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info dynamically."""
        device_id = self.coordinator.device.serial if self.coordinator.device.serial != "Uninitialized" else self.coordinator.address
        return {
            "identifiers": {(DOMAIN, device_id)},
            "name": self.coordinator.device.name_readable,
            "manufacturer": "Petkit",
            "model": self.coordinator.device.product_name,
            "sw_version": str(self.coordinator.device.firmware),
        }

class PetkitPowerSwitch(PetkitSwitchBase):
    """Power switch for the water fountain."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the power switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.serial}_power"
        self._attr_name = f"{coordinator.device.name_readable} Power"
        self._attr_icon = "mdi:power"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if the fountain is on."""
        power_status = self.coordinator.current_data.get("status", {}).get("power_status")
        return power_status == POWER_ON if power_status is not None else None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fountain on."""
        current_mode = self.coordinator.current_data.get("status", {}).get("mode", MODE_NORMAL)
        await self.coordinator.async_set_device_mode(POWER_ON, current_mode)
        await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fountain off."""
        current_mode = self.coordinator.current_data.get("status", {}).get("mode", MODE_NORMAL)
        await self.coordinator.async_set_device_mode(POWER_OFF, current_mode)
        await self.coordinator.async_request_refresh()

class PetkitSmartModeSwitch(PetkitSwitchBase):
    """Smart mode switch for the water fountain."""
    
    def __init__(self, coordinator: PetkitBLECoordinator) -> None:
        """Initialize the smart mode switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.serial}_smart_mode"
        self._attr_name = f"{coordinator.device.name_readable} Smart Mode"
        self._attr_icon = "mdi:brain"
    
    @property
    def is_on(self) -> bool | None:
        """Return true if smart mode is enabled."""
        mode = self.coordinator.current_data.get("status", {}).get("mode")
        return mode == MODE_SMART if mode is not None else None
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable smart mode."""
        current_power = self.coordinator.current_data.get("status", {}).get("power_status", POWER_ON)
        await self.coordinator.async_set_device_mode(current_power, MODE_SMART)
        await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable smart mode (switch to normal mode)."""
        current_power = self.coordinator.current_data.get("status", {}).get("power_status", POWER_ON)
        await self.coordinator.async_set_device_mode(current_power, MODE_NORMAL)
        await self.coordinator.async_request_refresh()