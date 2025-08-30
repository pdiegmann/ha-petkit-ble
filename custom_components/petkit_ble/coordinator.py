"""Data update coordinator for Petkit BLE integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.active_update_processor import ActiveBluetoothProcessorCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, CONF_ADDRESS
from .ha_bluetooth_adapter import HABluetoothAdapter

# Import the Petkit library modules (included in the integration)
import sys
import os

# Add current directory to path so we can import PetkitW5BLEMQTT
sys.path.insert(0, os.path.dirname(__file__))

from PetkitW5BLEMQTT.device import Device
from PetkitW5BLEMQTT.event_handlers import EventHandlers
from PetkitW5BLEMQTT.commands import Commands
from PetkitW5BLEMQTT.constants import Constants

_LOGGER = logging.getLogger(__name__)

class PetkitBLEData:
    """Data class for Petkit BLE device."""
    
    def __init__(self, device: Device) -> None:
        """Initialize the data."""
        self.device = device
        
    def update(self, service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        """Update device data from bluetooth service info."""
        # Update RSSI from advertisement
        if hasattr(self.device, '_rssi'):
            self.device.status = {"rssi": service_info.rssi}

class PetkitBLECoordinator(ActiveBluetoothProcessorCoordinator[PetkitBLEData]):
    """Petkit BLE data update coordinator using HA's Bluetooth integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.address = entry.data[CONF_ADDRESS]
        
        # Initialize Petkit BLE components with HA Bluetooth adapter
        self.device = Device(self.address)
        self.commands = Commands(ble_manager=None, device=self.device, logger=_LOGGER)
        self.event_handlers = EventHandlers(
            device=self.device, 
            commands=self.commands, 
            logger=_LOGGER
        )
        
        # Use HA Bluetooth adapter instead of direct BLE manager
        self.ble_manager = HABluetoothAdapter(
            hass=hass,
            address=self.address,
            event_handler=self.event_handlers,
            logger=_LOGGER
        )
        
        # Complete the circular references
        self.commands.ble_manager = self.ble_manager
        # Fix missing mac attribute in Commands class
        self.commands.mac = self.address
        
        # Set BLE manager reference in device for connection status access
        self.device.set_ble_manager(self.ble_manager)
        
        # Initialize data processor
        self.data = PetkitBLEData(self.device)
        
        # Define poll method for this instance
        async def _async_poll(service_info: bluetooth.BluetoothServiceInfoBleak) -> PetkitBLEData:
            """Poll the device for updated data."""
            try:
                # Device should already be initialized via _async_setup
                if not self._initialized:
                    _LOGGER.warning("Device not initialized during poll, attempting initialization")
                    await self._initialize_device()
                    
                # Get fresh device data using existing commands
                await self.commands.get_battery()
                await self.commands.get_device_update()
                await self.commands.get_device_state()
                
                # Update data object
                self.data.update(service_info)
                
                # Notify listeners of the update
                self.async_update_listeners()
                
                return self.data
                
            except Exception as err:
                _LOGGER.error("Error polling device: %s", err)
                raise UpdateFailed(f"Error polling device: {err}") from err

        def _needs_poll(service_info: bluetooth.BluetoothServiceInfoBleak, last_poll: float | None) -> bool:
            """Check if we need to poll the device."""
            # Always poll for active data updates
            return True
        
        super().__init__(
            hass,
            _LOGGER,
            address=self.address,
            mode=bluetooth.BluetoothScanningMode.ACTIVE,
            update_method=self.data.update,
            needs_poll_method=_needs_poll,
            poll_method=_async_poll,
            connectable=True,
        )
        
        self._consumer_task = None
        self._initialized = False
        self._listeners: set = set()

    async def _async_setup(self) -> None:
        """Set up the coordinator during first refresh."""
        await self._initialize_device()

    async def _initialize_device(self) -> None:
        """Initialize the BLE connection and device."""
        try:
            # Scan for devices first to populate connectiondata
            await self.ble_manager.scan()
            
            # Connect to the specific device using HA Bluetooth
            if not await self.ble_manager.connect_device(self.address):
                raise UpdateFailed(f"Could not connect to device {self.address}")
            
            # Start message consumer
            self._consumer_task = asyncio.create_task(
                self.ble_manager.message_consumer(self.address, Constants.WRITE_UUID)
            )
            
            # Start notifications for device updates
            await self.ble_manager.start_notifications(self.address, Constants.READ_UUID)
            
            # Initialize device data and connection using existing logic
            # Check if we have connection data before trying to initialize device data
            if self.address in self.ble_manager.connectiondata:
                self.commands.init_device_data()
            else:
                _LOGGER.warning(f\"No connection data for {self.address}, using defaults\")
                # Set basic device info manually
                self.device.name = \"Petkit Water Fountain\"
                self.device.name_readable = \"Petkit Water Fountain\"  
                self.device.product_name = \"Petkit BLE Water Fountain\"
                self.device.device_type = 14  # Default device type for W5
                self.device.type_code = 14
            
            await self.commands.init_device_connection()
            
            # Wait for device to be fully initialized
            retry_count = 0
            while self.device.serial == "Uninitialized" and retry_count < 10:
                _LOGGER.info("Device not initialized yet, waiting...")
                await asyncio.sleep(1)
                retry_count += 1
                
            if self.device.serial == "Uninitialized":
                raise UpdateFailed("Device initialization timed out")
            
            self._initialized = True
            _LOGGER.info("Device initialized successfully")
            
        except Exception as err:
            _LOGGER.error("Device initialization failed: %s", err)
            await self._cleanup()
            raise UpdateFailed(f"Device initialization failed: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and cleanup resources."""
        await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
                
        # Stop notifications and disconnect
        if self.address in self.ble_manager.connected_devices:
            await self.ble_manager.stop_notifications(self.address, Constants.READ_UUID)
            await self.ble_manager.disconnect_device(self.address)
            
        self._initialized = False

    async def async_set_device_mode(self, state: int, mode: int) -> None:
        """Set device mode (power and operation mode)."""
        await self.commands.set_device_mode(state, mode)
        
    async def async_reset_filter(self) -> None:
        """Reset the device filter."""
        await self.commands.set_reset_filter()
        
    async def async_set_device_config(self, config_data: list) -> None:
        """Set device configuration."""
        await self.commands.set_device_config(config_data)

    def async_add_listener(self, update_callback, context=None) -> callable:
        """Add a listener for data updates."""
        self._listeners.add(update_callback)
        
        def remove_listener():
            self._listeners.discard(update_callback)
        
        return remove_listener

    def async_remove_listener(self, update_callback) -> None:
        """Remove a listener."""
        self._listeners.discard(update_callback)

    def async_update_listeners(self) -> None:
        """Update all listeners."""
        for update_callback in self._listeners:
            update_callback()

    @property
    def current_data(self) -> dict[str, Any]:
        """Return the current device data for entities."""
        return {
            "status": self.device.status,
            "config": self.device.config,
            "info": self.device.info,
            "name": self.device.name_readable,
            "product_name": self.device.product_name,
            "firmware": self.device.firmware,
            "serial": self.device.serial,
        }