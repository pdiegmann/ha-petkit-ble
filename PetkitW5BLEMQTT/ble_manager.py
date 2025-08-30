from bleak import BleakScanner, BleakClient
from .constants import Constants
from .utils import Utils
from .device import Device
import asyncio
import logging
import time
from enum import Enum

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

class BLEManager:
    def __init__(self, event_handler, commands, logger, callback=None):
        self.connected_devices = {}
        self.available_devices = {}
        self.connectiondata = {}
        self.logger = logger
        self.queue = asyncio.Queue(10)
        self.callback = callback
        self.device = False
        self.event_handler = event_handler
        self.commands = commands
        
        # Connection status tracking
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._last_seen = None
        self._connection_attempts = 0
        self._last_connection_attempt = None
        self._connection_error = None
        self._retry_delay = 1.0  # Start with 1 second delay
        self._max_retry_delay = 60.0  # Maximum retry delay
        self._max_connection_attempts = 10
        self._last_logged_status = None  # Track last logged status to prevent spam

    async def scan(self):
        self.logger.info("Scanning for Petkit BLE devices...")
        devices = await BleakScanner.discover()
        self.available_devices = {dev.address: dev for dev in devices if "W4" in dev.name or "W5" in dev.name or "CTW2" in dev.name}
        for address, device in self.available_devices.items():
            self.logger.info(f"Found device: {device.name} ({address})")
            self.connectiondata[address] = device
        return self.available_devices

    async def connect_device(self, address):
        if address not in self.available_devices:
            self.logger.error(f"Device {address} not found")
            self._update_connection_status(ConnectionStatus.FAILED, f"Device {address} not found in scan results")
            return False
        
        try:
            # Update status based on whether this is initial connection or retry
            if self._connection_attempts == 0:
                self._update_connection_status(ConnectionStatus.CONNECTING)
            else:
                self._update_connection_status(ConnectionStatus.RECONNECTING)
            
            self._last_connection_attempt = time.time()
            
            client = BleakClient(address, timeout=65.0)
            await client.connect()
            
            self.connected_devices[address] = client
            self._update_connection_status(ConnectionStatus.CONNECTED)
            self._update_last_seen()
            
            await self.start_notifications(address, Constants.READ_UUID)
            return True
            
        except Exception as e:
            self._connection_attempts += 1
            error_msg = f"Connection attempt {self._connection_attempts} failed: {e}"
            
            if not self._should_attempt_retry():
                self._update_connection_status(ConnectionStatus.FAILED, error_msg)
            else:
                self._update_connection_status(ConnectionStatus.RECONNECTING, error_msg)
            
            return False

    async def disconnect_device(self, address):
        if address in self.connected_devices:
            try:
                client = self.connected_devices[address]
                
                if client.is_connected:
                    await client.stop_notify(Constants.READ_UUID)
                
                await client.disconnect()
                del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.DISCONNECTED)
                return True
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
                # Force removal from connected devices even if disconnect fails
                if address in self.connected_devices:
                    del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.DISCONNECTED, f"Disconnect error: {e}")
                return False
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def read_characteristic(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Reading characteristic {characteristic_uuid} from {address}")
            client = self.connected_devices[address]
            data = await client.read_gatt_char(characteristic_uuid)
            self.logger.info(f"Read data: {data}")
            return data
        else:
            self.logger.error(f"Device {address} not connected")
            return None

    async def write_characteristic(self, address, characteristic_uuid, data):
        if address in self.connected_devices:
            try:
                self.logger.info(f"Writing to characteristic {characteristic_uuid} on {address}")
                client = self.connected_devices[address]
                await client.write_gatt_char(characteristic_uuid, data)
                self.logger.info(f"Write complete")
                self._update_last_seen()
                return True
            except Exception as e:
                self.logger.error(f"Write failed: {e}")
                # Mark as disconnected so reconnection will be attempted
                if address in self.connected_devices:
                    del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.RECONNECTING, f"Write failed: {e}")
                return False
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def start_notifications(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Starting notifications for {characteristic_uuid} on {address}")
            client = self.connected_devices[address]
            await client.start_notify(characteristic_uuid, self._handle_notification_wrapper)
            self.logger.info(f"Notifications started for {characteristic_uuid} on {address}")
            return True
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def _handle_notification_wrapper(self, sender, data):
        # Update last seen timestamp on successful notification
        self._update_last_seen()
        await self.event_handler.handle_notification(sender, data)

    async def stop_notifications(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Stopping notifications for {characteristic_uuid} on {address}")
            client = self.connected_devices[address]
            await client.stop_notify(characteristic_uuid)
            self.logger.info(f"Notifications stopped for {characteristic_uuid} on {address}")
            return True
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def heartbeat(self, interval):
        while True:
            for address in list(self.connected_devices.keys()):
                try:
                    await self.commands.get_battery() # To update voltage
                    await self.commands.get_device_update()
                    
                    if self.queue.qsize() > 10: 
                        raise Exception("Queue size over threshold. Disconnecting...")
                    
                    # Update last seen on successful heartbeat operations
                    self._update_last_seen()
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    # Only log error once per connection failure
                    if self._connection_status != ConnectionStatus.RECONNECTING:
                        self.logger.error(f"Heartbeat failed: {e}")
                    
                    await self.disconnect_device(address)
                    
                    # Implement retry logic with exponential backoff
                    await self._attempt_reconnection_with_backoff(address)

    async def message_consumer(self, address, characteristic_uuid):
        while True:
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

            try:
                message = await self.queue.get()
                success = await self.write_characteristic(address, characteristic_uuid, message)
                if success:
                    self._update_last_seen()
                self.queue.task_done()
            except Exception as e:
                self.logger.error(f"Message consumer error: {e}")
                self.queue.task_done()
                await self._attempt_reconnection_with_backoff(address)
    
    async def _attempt_reconnection_with_backoff(self, address):
        """Attempt reconnection with exponential backoff."""
        if not self._should_attempt_retry():
            return
        
        retry_delay = self._calculate_retry_delay()
        
        # Only log the delay if status changed (prevents spam)
        if self._connection_status != ConnectionStatus.RECONNECTING:
            self.logger.info(f"Waiting {retry_delay:.1f}s before reconnection attempt")
        
        await asyncio.sleep(retry_delay)
        
        success = await self.connect_device(address)
        if not success and self._should_attempt_retry():
            # Will be called again by the consumer/heartbeat loop
            pass
    
    def reset_connection_state(self):
        """Reset connection tracking state for clean restart."""
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._connection_attempts = 0
        self._retry_delay = 1.0
        self._connection_error = None
        self._last_connection_attempt = None
        self._last_logged_status = None

    async def message_producer(self, message):
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
                self.logger.info(f"Connection established - Status: {status.value}")
                self._connection_attempts = 0  # Reset on successful connection
                self._retry_delay = 1.0  # Reset retry delay
            elif status == ConnectionStatus.DISCONNECTED:
                self.logger.info(f"Connection closed - Status: {status.value}")
            elif status == ConnectionStatus.CONNECTING:
                self.logger.info(f"Attempting connection - Status: {status.value}")
            elif status == ConnectionStatus.RECONNECTING:
                self.logger.info(f"Reconnecting (attempt {self._connection_attempts + 1}/{self._max_connection_attempts}) - Status: {status.value}")
            elif status == ConnectionStatus.FAILED:
                self.logger.error(f"Connection failed after {self._max_connection_attempts} attempts - Status: {status.value}")
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
