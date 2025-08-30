import argparse
import asyncio
import logging
from PetkitW5BLEMQTT import BLEManager, Constants, Device, EventHandlers, Commands, Logger, Utils

class Manager:
    def __init__(self, address, logging_level=logging.INFO):
        self.setup_logging(logging_level)
        self.logger = logging.getLogger("PetkitW5BLEMQTT")
        debug = logging_level == logging.DEBUG  # Determine if debug logging is enabled

        self.address = address
        self.device = Device(self.address)

        # Correct order of instantiation
        self.commands = Commands(ble_manager=None, device=self.device, logger=self.logger)
        self.event_handlers = EventHandlers(device=self.device, commands=self.commands, logger=self.logger)
        self.ble_manager = BLEManager(event_handler=self.event_handlers, commands=self.commands, logger=self.logger)
        self.ble_manager.manager = self
        
        # Update ble_manager in commands now that it is created
        self.commands.ble_manager = self.ble_manager
        
        # Previously: MQTT client initialization and data forwarding setup

    def setup_logging(self, logging_level):
        logging.basicConfig(level=logging_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    async def run(self, address):
        await self.ble_manager.scan()
        
        self.logger.info(f"Connecting...")
        
        if await self.ble_manager.connect_device(address):
            self.logger.info(f"Connected.")
            
            # Start the producer and consumer tasks
            consumer = asyncio.create_task(self.ble_manager.message_consumer(address, Constants.WRITE_UUID))

            # Init the device
            self.commands.init_device_data()
            
            try:
                # Connect to the device
                await self.commands.init_device_connection()
                
                while self.device.serial == "Uninitialized":
                    self.logger.info(f"Device not initialized yet, waiting...")
                    await asyncio.sleep(1)
                
                heartbeat = asyncio.create_task(self.ble_manager.heartbeat(60))

                # Previously: MQTT discovery payloads published and command subscriptions established
                while True:
                    await asyncio.sleep(1)  # Example interval for ad-hoc message sending

            except KeyboardInterrupt:
                # Handling cleanup on keyboard interrupt
                self.logger.info("Interrupted, cleaning up...")            
                
                # Wait for queue to be empty and disconnect the device
                await self.ble_manager.queue.join()
                await self.ble_manager.disconnect_device(address)
            finally:
                # Previously: MQTT offline status published and connection closed
                pass

    async def restart_run(self, address = None):
        if address is None:
            address = self.address
        
        self.logger.info("Restarting run function due to inactivity.")

        # Reset initialization_state and software_version
        self.device.initialization_state = False
        self.device.info = {'software_version': None}
        
        await self.run(address)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BLE Manager")
    parser.add_argument("--address", type=str, required=True, help="BLE device address")
    # Previously: MQTT configuration arguments
    parser.add_argument("--logging_level", type=str, default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser.parse_args()

    # Previously: MQTT settings dictionary creation

    logging_level = getattr(logging, args.logging_level.upper(), logging.INFO)

    manager = Manager(args.address, logging_level=logging_level)
    asyncio.run(manager.run(args.address))