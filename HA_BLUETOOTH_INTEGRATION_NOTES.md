# Home Assistant Bluetooth Integration Changes

This document summarizes the key changes made to integrate the Petkit BLE component with Home Assistant's shared Bluetooth system.

## Key Changes Made

### 1. Manifest Updates (`manifest.json`)
- Added `"dependencies": ["bluetooth_adapters"]` for multi-dongle support
- Added `"requirements": ["bleak==0.20.2", "bleak-retry-connector>=3.0.0"]`
- Added `"bluetooth": [{"connectable": true}]` to declare Bluetooth usage

### 2. Home Assistant Bluetooth Adapter (`ha_bluetooth_adapter.py`)
**Purpose**: Bridge between HA's Bluetooth APIs and existing Petkit library

**Key Features**:
- Uses `homeassistant.components.bluetooth` APIs instead of direct `bleak`
- Implements same interface as existing `BLEManager` for compatibility
- Uses `BluetoothClient` with `bleak-retry-connector` for robust connections
- Integrates with HA's device discovery system

**Methods Adapted**:
- `scan()` - Uses HA's `bluetooth.async_discovered_service_info()`
- `connect_device()` - Uses `bluetooth.async_ble_device_from_address()` and `BluetoothClient`
- All BLE operations routed through HA's shared Bluetooth system

### 3. Coordinator Redesign (`coordinator.py`)
**Changed from**: `DataUpdateCoordinator`
**Changed to**: `ActiveBluetoothProcessorCoordinator`

**Key Changes**:
- Uses HA's `ActiveBluetoothProcessorCoordinator` for proper Bluetooth integration
- Implements `_async_poll()` method for active device polling
- Uses `HABluetoothAdapter` instead of direct `BLEManager`
- Maintains existing Petkit communication protocols without modification
- Added `commands.mac = self.address` to fix missing attribute in existing library

**Benefits**:
- Proper integration with HA's Bluetooth scanning and discovery
- Automatic advertisement processing and device availability tracking
- Shared dongle access with other integrations

### 4. Config Flow Updates (`config_flow.py`)
**Key Changes**:
- Uses HA's `bluetooth.async_discovered_service_info()` instead of custom scanning
- Integrates with HA's automatic Bluetooth discovery flow
- Uses `BluetoothClient` for connection testing instead of direct `BleakClient`
- Proper error handling for HA Bluetooth system

**Discovery Flow**:
- Automatic: Devices appear in HA's discovered devices list
- Manual: Users select from HA's Bluetooth-discovered devices
- Connection validation through HA's Bluetooth system

### 5. Entity Updates
**Changed**: All sensors, switches, and binary sensors updated to use `coordinator.current_data` instead of `coordinator.data`

**Reason**: `ActiveBluetoothProcessorCoordinator` uses different data access patterns than standard `DataUpdateCoordinator`

## Compliance with HA Bluetooth Guidelines

### ✅ What We Did Right
1. **Never talk to dongles directly** - All BLE access goes through HA's Bluetooth integration
2. **Use HA's shared scanner** - No custom BLE scanning, uses HA's discovery system
3. **Proper coordinator** - Uses `ActiveBluetoothProcessorCoordinator` for connection-based devices
4. **Bluetooth adapters dependency** - Declared in manifest.json
5. **BluetoothClient usage** - Uses HA's `BluetoothClient` instead of raw `BleakClient`
6. **Retry connector** - Uses `bleak-retry-connector` for robust connections

### ✅ Integration Benefits
1. **Shared Dongle Access** - Multiple integrations can use same Bluetooth adapter safely
2. **Automatic Discovery** - Devices appear in HA's discovery system automatically
3. **Connection Management** - HA handles connection routing and adapter selection
4. **Resource Cleanup** - Proper resource management following HA patterns
5. **Multi-Adapter Support** - Works with multiple Bluetooth adapters automatically

### ✅ Preserved Functionality
- **Zero modifications** to existing PetkitW5BLEMQTT communication library
- **Full compatibility** with Petkit device communication protocols
- **All existing features** preserved (sensors, switches, services)
- **Same device capabilities** - power control, filter management, etc.

## Architecture Flow

```
Home Assistant Bluetooth Discovery
           ↓
    Config Flow (HA Integration)
           ↓
ActiveBluetoothProcessorCoordinator
           ↓
    HABluetoothAdapter
           ↓
Existing Petkit Library (Unmodified)
           ↓
      Petkit Device
```

## Testing Considerations

1. **Multiple Integrations** - Test with other Bluetooth integrations active
2. **Multi-Adapter Setup** - Test with multiple Bluetooth adapters
3. **Connection Resilience** - Test connection recovery and retry logic
4. **Discovery Flow** - Test both automatic and manual device discovery
5. **Resource Cleanup** - Verify proper cleanup on integration removal

## Migration Impact

**For Users**:
- Existing integrations need to be removed and re-added
- Devices will now appear in HA's automatic discovery
- Better compatibility with other Bluetooth integrations

**For Developers**:
- Integration now follows HA Bluetooth best practices
- Proper shared access to Bluetooth resources
- Future-proof against HA Bluetooth system changes

## Key Files Modified

1. `manifest.json` - Added Bluetooth dependencies and declarations
2. `ha_bluetooth_adapter.py` - NEW: HA Bluetooth adapter layer
3. `coordinator.py` - Complete redesign using ActiveBluetoothProcessorCoordinator
4. `config_flow.py` - Updated to use HA's Bluetooth discovery
5. All entity files - Updated data access patterns
6. `README_HOMEASSISTANT.md` - Updated documentation

The integration now properly shares Bluetooth resources with Home Assistant and other integrations while maintaining full compatibility with Petkit water fountains.