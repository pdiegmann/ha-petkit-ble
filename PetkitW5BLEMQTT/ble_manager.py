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
        self._last_logged_status = None  # Track last logged status to prevent spam
        
        # Persistent connection management
        self._target_address = None
        self._connection_monitor_task = None
        self._should_maintain_connection = False
        self._connection_lost_event = asyncio.Event()
        self._stop_event = asyncio.Event()

    async def scan(self):
        self.logger.info("Scanning for Petkit BLE devices...")
        devices = await BleakScanner.discover()
        self.available_devices = {dev.address: dev for dev in devices if "W4" in dev.name or "W5" in dev.name or "CTW2" in dev.name}
        for address, device in self.available_devices.items():
            self.logger.info(f"Found device: {device.name} ({address})")
            self.connectiondata[address] = device
        return self.available_devices

    async def connect_device(self, address, start_monitoring=True):
        """Connect to a device with optional persistent connection monitoring."""
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
            
            # Start persistent connection monitoring if requested
            if start_monitoring:
                await self.start_persistent_connection(address)
            
            return True
            
        except Exception as e:
            self._connection_attempts += 1
            error_msg = f"Connection attempt {self._connection_attempts} failed: {e}"
            self._update_connection_status(ConnectionStatus.RECONNECTING, error_msg)
            
            # Signal connection lost for instant retry
            self._connection_lost_event.set()
            
            return False

    async def disconnect_device(self, address, stop_monitoring=True):
        """Disconnect from a device with optional monitoring stop."""
        # Stop persistent monitoring if requested
        if stop_monitoring:
            await self.stop_persistent_connection()
        
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
            try:
                self.logger.info(f"Reading characteristic {characteristic_uuid} from {address}")
                client = self.connected_devices[address]
                data = await client.read_gatt_char(characteristic_uuid)
                self.logger.info(f"Read data: {data}")
                self._update_last_seen()
                return data
            except Exception as e:
                self.logger.error(f"Read failed: {e}")
                # Mark as disconnected and signal connection lost for instant retry
                if address in self.connected_devices:
                    del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.RECONNECTING, f"Read failed: {e}")
                self._connection_lost_event.set()
                return None
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
                # Mark as disconnected and signal connection lost for instant retry
                if address in self.connected_devices:
                    del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.RECONNECTING, f"Write failed: {e}")
                self._connection_lost_event.set()
                return False
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def start_notifications(self, address, characteristic_uuid):
        if address in self.connected_devices:
            try:
                self.logger.info(f"Starting notifications for {characteristic_uuid} on {address}")
                client = self.connected_devices[address]
                await client.start_notify(characteristic_uuid, self._handle_notification_wrapper)
                self.logger.info(f"Notifications started for {characteristic_uuid} on {address}")
                return True
            except Exception as e:
                self.logger.error(f"Start notifications failed: {e}")
                # Mark as disconnected and signal connection lost for instant retry
                if address in self.connected_devices:
                    del self.connected_devices[address]
                self._update_connection_status(ConnectionStatus.RECONNECTING, f"Notifications failed: {e}")
                self._connection_lost_event.set()
                return False
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def _handle_notification_wrapper(self, sender, data):
        try:
            # Update last seen timestamp on successful notification
            self._update_last_seen()
            await self.event_handler.handle_notification(sender, data)
        except Exception as e:
            self.logger.error(f"Notification handler error: {e}")
            # Signal connection issue for immediate reconnection attempt
            self._connection_lost_event.set()

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
                    
                    await self.disconnect_device(address, stop_monitoring=False)
                    
                    # Signal connection lost for instant retry
                    self._connection_lost_event.set()
                    break

    async def message_consumer(self, address, characteristic_uuid):
        while not self._stop_event.is_set():
            if not self.connected_devices.get(address):
                # Wait for connection to be re-established by persistent monitor
                await asyncio.sleep(0.1)
                continue

            try:
                # Wait for message with short timeout to allow checking connection status
                try:
                    message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                    
                success = await self.write_characteristic(address, characteristic_uuid, message)
                if success:
                    self._update_last_seen()
                self.queue.task_done()
            except Exception as e:
                self.logger.error(f"Message consumer error: {e}")
                try:
                    self.queue.task_done()
                except ValueError:
                    pass  # Queue might be empty
                # Connection monitor will handle reconnection
    
    async def start_persistent_connection(self, address):
        """Start persistent connection monitoring for instant reconnection."""
        self._target_address = address
        self._should_maintain_connection = True
        
        # Stop any existing monitor
        if self._connection_monitor_task and not self._connection_monitor_task.done():
            self._connection_monitor_task.cancel()
        
        # Start connection monitor
        self._connection_monitor_task = asyncio.create_task(self._connection_monitor())
        self.logger.info(f"Started persistent connection monitoring for {address}")
    
    async def stop_persistent_connection(self):
        """Stop persistent connection monitoring."""
        self._should_maintain_connection = False
        self._stop_event.set()
        
        if self._connection_monitor_task and not self._connection_monitor_task.done():
            self._connection_monitor_task.cancel()
            try:
                await self._connection_monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped persistent connection monitoring")
    
    async def _connection_monitor(self):
        """Continuously monitor connection and reconnect instantly when needed."""
        while self._should_maintain_connection and not self._stop_event.is_set():
            try:
                # Check if we're connected
                if self._target_address not in self.connected_devices:
                    self.logger.info("Connection lost, attempting instant reconnection...")
                    
                    # Try to reconnect immediately
                    success = await self.connect_device(self._target_address, start_monitoring=False)
                    
                    if not success:
                        # If immediate reconnection fails, try again after very short delay
                        await asyncio.sleep(0.1)
                        continue
                    else:
                        self.logger.info("Reconnection successful")
                        self._connection_attempts = 0  # Reset on successful connection
                        self._connection_lost_event.clear()
                
                # Check connection health
                elif self._target_address in self.connected_devices:
                    client = self.connected_devices[self._target_address]
                    if not client.is_connected:
                        self.logger.warning("BLE client reports not connected, cleaning up...")
                        del self.connected_devices[self._target_address]
                        self._update_connection_status(ConnectionStatus.RECONNECTING, "Client disconnected")
                        continue
                
                # Wait for connection lost event or timeout
                try:
                    await asyncio.wait_for(self._connection_lost_event.wait(), timeout=1.0)
                    self._connection_lost_event.clear()
                except asyncio.TimeoutError:
                    pass  # Normal timeout, continue monitoring
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection monitor error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retry
    
    def reset_connection_state(self):
        """Reset connection tracking state for clean restart."""
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._connection_attempts = 0
        self._connection_error = None
        self._last_connection_attempt = None
        self._last_logged_status = None
        self._connection_lost_event.clear()
        self._stop_event.clear()

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
            elif status == ConnectionStatus.DISCONNECTED:
                self.logger.info(f"Connection closed - Status: {status.value}")
            elif status == ConnectionStatus.CONNECTING:
                self.logger.info(f"Attempting connection - Status: {status.value}")
            elif status == ConnectionStatus.RECONNECTING:
                self.logger.info(f"Reconnecting (attempt {self._connection_attempts + 1}) - Status: {status.value}")
            elif status == ConnectionStatus.FAILED:
                self.logger.error(f"Connection failed - Status: {status.value}")
                if error:
                    self.logger.error(f"Last error: {error}")
            
            self._last_logged_status = status
    
    def _update_last_seen(self):
        """Update last seen timestamp."""
        self._last_seen = time.time()
    
    @property
    def is_monitoring_connection(self):
        """Check if persistent connection monitoring is active."""
        return self._should_maintain_connection and self._connection_monitor_task and not self._connection_monitor_task.done()
