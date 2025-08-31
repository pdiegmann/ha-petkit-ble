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
                # Only poll if device is already initialized (prevent duplicate initialization)
                if not self._initialized:
                    _LOGGER.debug("Device not yet initialized, skipping poll")
                    return self.data
                
                # Check if device is still connected before polling
                if not self.ble_manager.connected_devices.get(self.address):
                    _LOGGER.debug("Device not connected during poll, skipping")
                    return self.data
                    
                # Get fresh device data using existing commands with timing
                _LOGGER.debug("Polling device for data updates")
                
                await self.commands.get_battery()
                await asyncio.sleep(0.4)  # Allow time for response
                
                await self.commands.get_device_state()
                await asyncio.sleep(0.4)
                
                await self.commands.get_device_update() 
                await asyncio.sleep(0.6)  # Longer wait for final response
                
                # Update data object
                self.data.update(service_info)
                
                # Notify listeners of the update
                self.async_update_listeners()
                
                _LOGGER.debug("Device poll completed")
                return self.data
                
            except Exception as err:
                _LOGGER.debug(f"Error polling device: {err}")
                # Don't raise UpdateFailed - just return existing data
                # This prevents the coordinator from failing completely
                return self.data

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
        self._initialization_task = None

    async def async_start(self) -> None:
        """Start the coordinator and immediately initialize connection."""
        # Start the base coordinator first (not async in ActiveBluetoothProcessorCoordinator)
        super().async_start()
        
        # Immediately attempt device initialization regardless of BT discovery
        if not self._initialized:
            self._initialization_task = asyncio.create_task(self._initialization_loop())
        
    async def _initialization_loop(self) -> None:
        """Continuously attempt device initialization until successful."""
        retry_count = 0
        # No max retries - keep trying indefinitely
        
        while not self._initialized:
            try:
                _LOGGER.info(f"Initialization attempt {retry_count + 1}")
                await self._initialize_device()
                if self._initialized:
                    _LOGGER.info("Device initialization successful")
                    break
            except Exception as err:
                _LOGGER.warning(f"Initialization attempt {retry_count + 1} failed: {err}")
                
            retry_count += 1
            
            # Use immediate retry with minimal delays
            if retry_count < 5:
                delay = 0.5  # 500ms for first 5 attempts
            elif retry_count < 10:
                delay = 1.0  # 1 second for next 5 attempts  
            elif retry_count < 20:
                delay = 2.0  # 2 seconds for next 10 attempts
            else:
                delay = 5.0  # 5 seconds afterwards
            
            _LOGGER.debug(f"Waiting {delay}s before next initialization attempt...")
            await asyncio.sleep(delay)

    async def _async_setup(self) -> None:
        """Set up the coordinator during first refresh."""
        await self._initialize_device()

    async def _initialize_device(self) -> None:
        """Initialize the BLE connection and device."""
        try:
            _LOGGER.info(f"Initializing BLE connection to device {self.address}")
            
            # Scan for devices first to populate connectiondata
            _LOGGER.info("Scanning for Petkit devices...")
            await self.ble_manager.scan()
            
            # Connect to the specific device using HA Bluetooth
            _LOGGER.info(f"Attempting to connect to device {self.address}")
            
            # Enable immediate reconnection mode
            if hasattr(self.ble_manager, '_immediate_reconnect'):
                self.ble_manager._immediate_reconnect = True
            
            if not await self.ble_manager.connect_device(self.address):
                raise UpdateFailed(f"Could not connect to device {self.address}")
            
            # Start message consumer
            _LOGGER.info("Starting message consumer...")
            self._consumer_task = asyncio.create_task(
                self.ble_manager.message_consumer(self.address, Constants.WRITE_UUID)
            )
            
            # Start notifications for device updates
            _LOGGER.info("Starting BLE notifications...")
            await self.ble_manager.start_notifications(self.address, Constants.READ_UUID)
            
            # Allow BLE stack to stabilize after connection
            _LOGGER.debug("Waiting for BLE stack to stabilize...")
            await asyncio.sleep(1.0)  # Increased to 1 second for better stability
            
            # Verify client is actually ready for writes
            client = self.ble_manager.connected_devices.get(self.address)
            if client and hasattr(client, 'is_connected'):
                retry_count = 0
                while not client.is_connected and retry_count < 5:
                    _LOGGER.debug(f"Client not ready, waiting... (attempt {retry_count + 1}/5)")
                    await asyncio.sleep(0.2)
                    retry_count += 1
                    
                if not client.is_connected:
                    raise UpdateFailed("Client not ready after 5 attempts")
                    
                _LOGGER.debug("Client verified ready for communication")
            
            # Initialize device data and connection using existing logic
            # Check if we have connection data before trying to initialize device data
            if self.address in self.ble_manager.connectiondata:
                _LOGGER.info("Using discovered connection data for device initialization")
                self.commands.init_device_data()
            else:
                _LOGGER.warning(f"No connection data for {self.address}, using defaults")
                # Set basic device info manually
                self.device.name = "Petkit Water Fountain"
                self.device.name_readable = "Petkit Water Fountain"  
                self.device.product_name = "Petkit BLE Water Fountain"
                self.device.device_type = 14  # Default device type for W5
                self.device.type_code = 14
            
            _LOGGER.info("Performing minimal device initialization...")
            
            # Instead of full init_device_connection(), do minimal required initialization
            try:
                # Get basic device details first
                _LOGGER.debug("Getting device details...")
                await self.commands.get_device_details()
                await asyncio.sleep(1.0)
                
                # Initialize device if needed
                if not hasattr(self.device, 'device_initialized') or not self.device.device_initialized:
                    _LOGGER.debug("Initializing device...")
                    await self.commands.init_device()
                    await asyncio.sleep(1.5)
                
                # Get basic device info  
                _LOGGER.debug("Getting device info...")
                await self.commands.get_device_info()
                await asyncio.sleep(0.75)
                
                _LOGGER.info("Minimal device initialization completed")
                
            except Exception as init_err:
                _LOGGER.warning(f"Minimal initialization failed: {init_err}")
                # Continue anyway - we'll try to get data without full initialization
            
            # Set basic device information directly since communication is working
            if self.device.serial == "Uninitialized":
                self.device.serial = f"PETKIT_{self.address.replace(':', '')[-6:]}"
                
            if not hasattr(self.device, 'name') or not self.device.name or self.device.name == "Uninitialized":
                self.device.name = f"Petkit Water Fountain"
                self.device.name_readable = f"Petkit Water Fountain ({self.address})"
                self.device.product_name = "Petkit BLE Water Fountain"
            
            _LOGGER.info(f"Set device info: serial='{self.device.serial}', name='{self.device.name_readable}'")
            
            # Since we've set the device info directly, mark as initialized immediately
            self._initialized = True
            _LOGGER.info(f"Device initialized successfully: {self.device.serial}")
            
            # Force an update to notify Home Assistant that device is ready
            self.async_update_listeners()
            _LOGGER.info("Notified Home Assistant that device is ready")
            
        except Exception as err:
            import traceback
            _LOGGER.error("Device initialization failed: %s", err)
            _LOGGER.debug("Full traceback:\n%s", traceback.format_exc())
            await self._cleanup()
            # Don't raise here - let the system retry later
            # This prevents the integration from failing completely on startup

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
        
        if self._initialization_task and not self._initialization_task.done():
            self._initialization_task.cancel()
            # Don't await cancelled task, just let it clean up
            try:
                # Give it a brief moment to process the cancellation
                await asyncio.sleep(0.1)
            except Exception as e:
                _LOGGER.debug(f"Error during initialization task cancellation: {e}")
                
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
    
    async def async_request_refresh(self) -> None:
        """Request a fresh update from the device."""
        if not self._initialized:
            _LOGGER.debug("Device not initialized, skipping refresh request")
            return
            
        try:
            # Check if device is still connected before attempting commands
            if not self.ble_manager.connected_devices.get(self.address):
                _LOGGER.warning("Device not connected during refresh request, triggering immediate reconnection")
                # Don't wait for reconnection to complete, just trigger it
                asyncio.create_task(self._attempt_reconnection())
                return
            
            # Get fresh device data using existing commands with delays for BLE stability
            _LOGGER.debug("Requesting device data refresh")
            
            await self.commands.get_battery()
            await asyncio.sleep(0.5)  # Small delay between commands for BLE stability
            
            await self.commands.get_device_state() 
            await asyncio.sleep(0.5)
            
            await self.commands.get_device_update()
            await asyncio.sleep(0.3)
            
            # Allow time for responses to be processed
            await asyncio.sleep(1.0)
            
            # Notify all listeners that data has been updated
            self.async_update_listeners()
            _LOGGER.debug("Device data refresh completed")
            
        except Exception as err:
            _LOGGER.warning("Failed to refresh device data: %s", err)
            # Don't raise the exception - just log the warning
            # This prevents the switch operation from failing completely
    
    async def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to the device."""
        try:
            _LOGGER.info("Attempting immediate reconnection to device")
            
            # Enable immediate reconnection mode in adapter
            if hasattr(self.ble_manager, '_immediate_reconnect'):
                self.ble_manager._immediate_reconnect = True
            
            # Use the immediate reconnection loop
            if hasattr(self.ble_manager, '_immediate_reconnection_loop'):
                await self.ble_manager._immediate_reconnection_loop(self.address)
                
                # If reconnected, restart message consumer
                if self.address in self.ble_manager.connected_devices:
                    if self._consumer_task and not self._consumer_task.done():
                        self._consumer_task.cancel()
                    
                    self._consumer_task = asyncio.create_task(
                        self.ble_manager.message_consumer(self.address, Constants.WRITE_UUID)
                    )
                    await self.ble_manager.start_notifications(self.address, Constants.READ_UUID)
                    _LOGGER.info("Device reconnection successful")
                else:
                    _LOGGER.warning("Device reconnection in progress...")
            else:
                # Fallback to standard reconnection
                if await self.ble_manager.connect_device(self.address):
                    # Restart message consumer and notifications
                    if self._consumer_task and not self._consumer_task.done():
                        self._consumer_task.cancel()
                    
                    self._consumer_task = asyncio.create_task(
                        self.ble_manager.message_consumer(self.address, Constants.WRITE_UUID)
                    )
                    await self.ble_manager.start_notifications(self.address, Constants.READ_UUID)
                    _LOGGER.info("Device reconnection successful")
                else:
                    _LOGGER.error("Device reconnection failed")
        except Exception as err:
            _LOGGER.error(f"Error during reconnection attempt: {err}")

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