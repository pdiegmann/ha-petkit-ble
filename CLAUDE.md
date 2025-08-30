# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PetkitW5BLEMQTT is a Python library for controlling Petkit W5 series water fountains via Bluetooth Low Energy (BLE). The library enables local control without cloud dependencies.

## Core Architecture

### Main Components

- **Manager** (`main.py`): Orchestrates the entire system, handles argument parsing, and coordinates BLE operations
- **BLEManager** (`ble_manager.py`): Manages Bluetooth Low Energy connections, device scanning, and message queuing
- **Device** (`device.py`): State management with status, config, and info properties; handles device attributes and settings
- **Commands** (`commands.py`): Device command interface for initialization, control operations, and data retrieval
- **EventHandlers** (`event_handlers.py`): Processes BLE notifications and updates device state
- **Parsers** (`parsers.py`): Data parsing utilities for BLE message interpretation
- **Utils** (`utils.py`): Utility functions for data processing and conversion

### Key Design Patterns

**Async/Await Architecture**: All BLE operations are asynchronous using asyncio
**State Management**: Device state is centralized in the Device class with property-based access
**Message Queuing**: BLE operations use an asyncio.Queue for ordered message processing
**Event-Driven**: Uses event handlers to process BLE notifications and update device state
**Dependency Injection**: Components receive their dependencies through constructor parameters

### Communication Flow

1. BLEManager scans for Petkit devices (W4, W5, CTW2 series)
2. Manager establishes BLE connection and initializes device
3. Commands class handles device initialization and data retrieval
4. EventHandlers processes incoming BLE notifications and updates device state
5. Continuous heartbeat maintains BLE connection

## Development Commands

### Running the Application

```bash
# Basic BLE operation
python main.py --address "A1:B2:C3:D4:E5:F6"

# With debug logging
python main.py --address "A1:B2:C3:D4:E5:F6" --logging_level "DEBUG"
```

### Installing Dependencies

```bash
# Install required packages
pip install -r PetkitW5BLEMQTT/requirements.txt

# Or install specific dependencies
pip install bleak>=1.0.1
```

### System Service Setup

The project includes a systemd service file (`petkitW5BLEMQTT.service`) for running as a system daemon. Note: This service file contains outdated MQTT parameters and should be updated for BLE-only operation.

## Key Technical Details

### BLE Communication

- Uses UUIDs from Constants class for read/write operations
- Implements custom message queuing for reliable BLE communication
- Handles device discovery by filtering for Petkit device names
- Maintains persistent connection with heartbeat mechanism

### Device State Management

Device class manages three categories of state:
- **Status**: Real-time device metrics (battery, warnings, runtime, etc.)
- **Config**: Device settings (smart mode timings, LED settings, DND settings)
- **Info**: Device information (firmware, serial, product name)

### Data Processing

- Processes BLE notifications through EventHandlers
- Updates device state automatically based on parsed data
- Maintains device status, configuration, and info properties
- Supports device control through Commands interface

### Error Handling

- Implements connection retry logic in BLEManager
- Graceful cleanup on KeyboardInterrupt
- Automatic device reconnection on communication failures

## Important Caveats

- Device ID and secret handling is incomplete (hardcoded values)
- Using CMD 73 may interfere with official app communication
- Do Not Disturb and Lights Out scheduling not yet supported
- Only tested with Petkit Eversweet 2 Solo
- MQTT functionality has been removed - library now provides BLE-only control

## File Structure Notes

- All core functionality is in the `PetkitW5BLEMQTT/` package
- `main.py` serves as the entry point and orchestrator
- No test suite is currently present
- Dependencies are minimal (bleak for BLE communication only)