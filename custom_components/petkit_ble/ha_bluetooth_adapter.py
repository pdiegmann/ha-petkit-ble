"""Home Assistant Bluetooth adapter for Petkit BLE integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import format_mac

_LOGGER = logging.getLogger(__name__)

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
                    mock_device = type('MockDevice', (), {
                        'name': service_info.name,
                        'address': service_info.address,
                        'rssi': service_info.rssi,
                        'details': {
                            'props': {
                                'RSSI': service_info.rssi,
                                'ServiceData': service_info.service_data or {}
                            }
                        }
                    })()
                    
                    petkit_devices[service_info.address] = mock_device
                    self.connectiondata[service_info.address] = mock_device
                    
            self.available_devices = petkit_devices
            
            for address, device in petkit_devices.items():
                self.logger.info(f"Found device: {device.name} ({address})")
                
            return petkit_devices
            
        except Exception as err:
            self.logger.error(f"Error scanning for devices: {err}")
            return {}

    async def connect_device(self, address: str) -> bool:
        """Connect to device using HA's bluetooth integration."""
        try:
            # Get BLE device from HA's bluetooth integration
            self._ble_device = bluetooth.async_ble_device_from_address(
                self.hass, address, connectable=True
            )
            
            if not self._ble_device:
                self.logger.error(f"Device {address} not found in HA bluetooth")
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
            self.logger.info(f"Connected to {address}")
            
            return True
            
        except Exception as err:
            self.logger.error(f"Failed to connect to {address}: {err}")
            return False

    async def disconnect_device(self, address: str) -> bool:
        """Disconnect from device."""
        try:
            if address in self.connected_devices:
                client = self.connected_devices[address]
                if hasattr(client, 'disconnect'):
                    await client.disconnect()
                del self.connected_devices[address]
                self.logger.info(f"Disconnected from {address}")
                return True
            return False
        except Exception as err:
            self.logger.error(f"Error disconnecting from {address}: {err}")
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
                return True
            else:
                self.logger.error(f"Device {address} not connected")
                return False
        except Exception as err:
            self.logger.error(f"Error writing to characteristic {characteristic_uuid}: {err}")
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
                    self.logger.warning(f"Device {address} not connected. Attempting to reconnect...")
                    if not await self.connect_device(address):
                        await asyncio.sleep(5)
                        continue
                    
                message = await self.queue.get()
                await self.write_characteristic(address, characteristic_uuid, message)
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as err:
                self.logger.error(f"Error in message consumer: {err}")
                await asyncio.sleep(1)

    async def message_producer(self, message: bytes) -> None:
        """Add message to queue for processing."""
        await self.queue.put(message)