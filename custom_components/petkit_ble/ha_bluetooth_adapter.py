"""Home Assistant Bluetooth adapter for Petkit BLE integration."""
from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable

from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import format_mac

_LOGGER = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

class HABluetoothAdapter:
    """Adapter to bridge HA's bluetooth integration with existing Petkit BLE library."""
    
    def __init__(self, hass: HomeAssistant, address: str, event_handler=None, logger=None):
        """Initialize the HA Bluetooth adapter."""
        self.hass = hass
        self.address = address
        self.event_handler = event_handler
        self.logger = logger or _LOGGER
        self.connected_devices = {}
        self.available_devices = {}
        self.connectiondata = {}
        self.queue = asyncio.Queue(10)
        self.callback = None
        self.device = False
        self._client = None
        self._ble_device = None
        
        # Connection status tracking (same as BLEManager)
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._last_seen = None
        self._connection_attempts = 0
        self._last_connection_attempt = None
        self._connection_error = None
        self._retry_delay = 1.0  # Start with 1 second delay
        self._max_retry_delay = 60.0  # Maximum retry delay
        self._max_connection_attempts = 10
        self._last_logged_status = None  # Track last logged status to prevent spam

    async def scan(self) -> dict[str, Any]:
        """Scan for Petkit BLE devices using HA's bluetooth integration."""
        try:
            # Get discovered devices from HA's bluetooth integration
            discovered_devices = bluetooth.async_discovered_service_info(self.hass)
            
            # Filter for Petkit devices
            petkit_devices = {}
            for service_info in discovered_devices:
                if service_info.name and any(
                    device_type in service_info.name 
                    for device_type in ["W4", "W5", "CTW2"]
                ):
                    # Create a mock device object compatible with existing library
                    # Convert service_data to the format expected by the library
                    # The combine_byte_arrays function expects a dict with .values()
                    service_data_dict = {}
                    if service_info.service_data:
                        service_data_dict = service_info.service_data
                    else:
                        # Default service data with device type identifier for W5
                        service_data_dict = {"default": [0, 0, 0, 0, 0, 206]}  # 206 = W5 device type
                    
                    mock_device = type('MockDevice', (), {
                        'name': service_info.name,
                        'address': service_info.address,
                        'rssi': service_info.rssi,
                        'details': {
                            'props': {
                                'RSSI': service_info.rssi,
                                'ServiceData': service_data_dict
                            }
                        }
                    })()
                    
                    petkit_devices[service_info.address] = mock_device
                    self.connectiondata[service_info.address] = mock_device
                    
            self.available_devices = petkit_devices
            
            for address, device in petkit_devices.items():
                self.logger.info(f"Found HA BLE device: {device.name} ({address})")
                
            return petkit_devices
            
        except Exception as err:
            self.logger.error(f"Error scanning for devices: {err}")
            return {}

    async def connect_device(self, address: str) -> bool:
        """Connect to device using HA's bluetooth integration."""
        try:
            # Update status based on whether this is initial connection or retry
            if self._connection_attempts == 0:
                self._update_connection_status(ConnectionStatus.CONNECTING)
            else:
                self._update_connection_status(ConnectionStatus.RECONNECTING)
            
            self._last_connection_attempt = time.time()
            
            # Get BLE device from HA's bluetooth integration
            self._ble_device = bluetooth.async_ble_device_from_address(
                self.hass, address, connectable=True
            )
            
            if not self._ble_device:
                error_msg = f"Device {address} not found in HA bluetooth"
                self._connection_attempts += 1
                
                if not self._should_attempt_retry():
                    self._update_connection_status(ConnectionStatus.FAILED, error_msg)
                else:
                    self._update_connection_status(ConnectionStatus.RECONNECTING, error_msg)
                return False
            
            # Use bleak-retry-connector directly with the BLE device
            from bleak import BleakClient
            self._client = await establish_connection(
                BleakClient,
                self._ble_device,
                address,
                timeout=30.0
            )
            
            self.connected_devices[address] = self._client
            self._update_connection_status(ConnectionStatus.CONNECTED)
            self._update_last_seen()
            
            return True
            
        except Exception as err:
            self._connection_attempts += 1
            error_msg = f"Connection attempt {self._connection_attempts} failed: {err}"
            
            if not self._should_attempt_retry():
                self._update_connection_status(ConnectionStatus.FAILED, error_msg)
            else:
                self._update_connection_status(ConnectionStatus.RECONNECTING, error_msg)
            
            return False

    async def disconnect_device(self, address: str) -> bool:
        """Disconnect from device."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                if hasattr(client, 'disconnect'):
                    await client.disconnect()
                del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.DISCONNECTED)
                return True
            return False
        except Exception as err:
            error_msg = f"Error disconnecting from {address}: {err}"
            # Force removal from connected devices even if disconnect fails
            if address in self.connected_devices:
                del self.connected_devices[address]
            self._update_connection_status(ConnectionStatus.DISCONNECTED, error_msg)
            return False

    async def read_characteristic(self, address: str, characteristic_uuid: str) -> bytes | None:
        """Read characteristic using HA's bluetooth client."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                data = await client.read_gatt_char(characteristic_uuid)
                self.logger.info(f"Read data from {characteristic_uuid}: {data}")
                return data
            else:
                self.logger.error(f"Device {address} not connected")
                return None
        except Exception as err:
            self.logger.error(f"Error reading characteristic {characteristic_uuid}: {err}")
            return None

    async def write_characteristic(self, address: str, characteristic_uuid: str, data: bytes) -> bool:
        """Write characteristic using HA's bluetooth client."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                await client.write_gatt_char(characteristic_uuid, data)
                self.logger.info(f"Write complete to {characteristic_uuid}")
                self._update_last_seen()
                return True
            else:
                self.logger.error(f"Device {address} not connected")
                return False
        except Exception as err:
            error_msg = f"Write failed: {err}"
            self.logger.error(f"Error writing to characteristic {characteristic_uuid}: {err}")
            # Mark as disconnected so reconnection will be attempted
            if address in self.connected_devices:
                del self.connected_devices[address]
            self._update_connection_status(ConnectionStatus.RECONNECTING, error_msg)
            return False

    async def start_notifications(self, address: str, characteristic_uuid: str) -> bool:
        """Start notifications using HA's bluetooth client."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                await client.start_notify(characteristic_uuid, self._handle_notification_wrapper)
                self.logger.info(f"Notifications started for {characteristic_uuid}")
                return True
            else:
                self.logger.error(f"Device {address} not connected")
                return False
        except Exception as err:
            self.logger.error(f"Error starting notifications for {characteristic_uuid}: {err}")
            return False

    async def stop_notifications(self, address: str, characteristic_uuid: str) -> bool:
        """Stop notifications using HA's bluetooth client."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                await client.stop_notify(characteristic_uuid)
                self.logger.info(f"Notifications stopped for {characteristic_uuid}")
                return True
            else:
                self.logger.error(f"Device {address} not connected")
                return False
        except Exception as err:
            self.logger.error(f"Error stopping notifications for {characteristic_uuid}: {err}")
            return False

    async def _handle_notification_wrapper(self, sender, data):
        """Wrapper for notification handling."""
        # Update last seen timestamp on successful notification
        self._update_last_seen()
        if self.event_handler:
            await self.event_handler.handle_notification(sender, data)

    async def heartbeat(self, interval: int) -> None:
        """Heartbeat method compatible with existing library."""
        # This will be called by the existing Commands class
        # The actual heartbeat logic should be handled by HA's coordinator
        pass

    async def message_consumer(self, address: str, characteristic_uuid: str) -> None:
        """Message consumer compatible with existing library."""
        while True:
            try:
                if not self.connected_devices.get(address):
                    # Only attempt reconnection if we should retry and we're not already trying
                    if (self._connection_status not in [ConnectionStatus.CONNECTING, ConnectionStatus.RECONNECTING] and
                        self._should_attempt_retry()):
                        
                        await self._attempt_reconnection_with_backoff(address)
                    elif self._connection_status == ConnectionStatus.FAILED:
                        # If connection failed, wait longer before checking again
                        await asyncio.sleep(30)
                    
                    await asyncio.sleep(1)
                    continue
                    
                message = await self.queue.get()
                success = await self.write_characteristic(address, characteristic_uuid, message)
                if success:
                    self._update_last_seen()
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as err:
                self.logger.error(f"Error in message consumer: {err}")
                self.queue.task_done()
                await self._attempt_reconnection_with_backoff(address)
                
    async def _attempt_reconnection_with_backoff(self, address):
        """Attempt reconnection with exponential backoff."""
        if not self._should_attempt_retry():
            return
        
        retry_delay = self._calculate_retry_delay()
        
        # Only log the delay if status changed (prevents spam)
        if self._connection_status != ConnectionStatus.RECONNECTING:
            self.logger.info(f"Waiting {retry_delay:.1f}s before HA BLE reconnection attempt")
        
        await asyncio.sleep(retry_delay)
        
        success = await self.connect_device(address)
        if not success and self._should_attempt_retry():
            # Will be called again by the consumer loop
            pass

    async def message_producer(self, message: bytes) -> None:
        """Add message to queue for processing."""
        await self.queue.put(message)
    
    @property
    def connection_status(self):
        """Get current connection status."""
        return self._connection_status.value
    
    @property
    def last_seen(self):
        """Get timestamp of last successful communication."""
        return self._last_seen
    
    @property
    def connection_attempts(self):
        """Get number of consecutive failed connection attempts."""
        return self._connection_attempts
    
    @property
    def connection_error(self):
        """Get last connection error message."""
        return self._connection_error
    
    def _update_connection_status(self, status, error=None):
        """Update connection status with controlled logging."""
        old_status = self._connection_status
        self._connection_status = status
        
        if error:
            self._connection_error = str(error)
        
        # Only log when status actually changes
        if old_status != status or self._last_logged_status != status:
            if status == ConnectionStatus.CONNECTED:
                self.logger.info(f"HA BLE Connection established - Status: {status.value}")
                self._connection_attempts = 0  # Reset on successful connection
                self._retry_delay = 1.0  # Reset retry delay
            elif status == ConnectionStatus.DISCONNECTED:
                self.logger.info(f"HA BLE Connection closed - Status: {status.value}")
            elif status == ConnectionStatus.CONNECTING:
                self.logger.info(f"HA BLE Attempting connection - Status: {status.value}")
            elif status == ConnectionStatus.RECONNECTING:
                self.logger.info(f"HA BLE Reconnecting (attempt {self._connection_attempts + 1}/{self._max_connection_attempts}) - Status: {status.value}")
            elif status == ConnectionStatus.FAILED:
                self.logger.error(f"HA BLE Connection failed after {self._max_connection_attempts} attempts - Status: {status.value}")
                if error:
                    self.logger.error(f"Last error: {error}")
            
            self._last_logged_status = status
    
    def _update_last_seen(self):
        """Update last seen timestamp."""
        self._last_seen = time.time()
    
    def _calculate_retry_delay(self):
        """Calculate exponential backoff delay."""
        delay = min(self._retry_delay * (2 ** self._connection_attempts), self._max_retry_delay)
        return delay
    
    def _should_attempt_retry(self):
        """Check if we should attempt another retry."""
        return self._connection_attempts < self._max_connection_attempts
    
    def reset_connection_state(self):
        """Reset connection tracking state for clean restart."""
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._connection_attempts = 0
        self._retry_delay = 1.0
        self._connection_error = None
        self._last_connection_attempt = None
        self._last_logged_status = None