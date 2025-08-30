# Petkit BLE Home Assistant Integration

This Home Assistant custom component provides local control of Petkit W5 series water fountains via Bluetooth Low Energy (BLE), without requiring cloud connectivity.

## Features

### Sensors
- **Battery Level**: Current battery percentage
- **Filter Status**: Filter percentage and days remaining
- **Pump Runtime**: Total and daily pump operation time
- **Water Statistics**: Purified water volume (total and daily)
- **Energy Consumption**: Total energy consumed by the device
- **Signal Strength**: BLE connection strength (RSSI)
- **Voltage**: Device voltage (diagnostic)

### Controls
- **Power Switch**: Turn fountain on/off
- **Smart Mode**: Enable/disable smart mode operation
- **Filter Reset**: Reset filter life indicator (via service call)

### Status Indicators
- **Filter Problem**: Alert for filter issues
- **Water Missing**: Low water warning
- **System Breakdown**: Device malfunction alert  
- **Running Status**: Fountain operation indicator

## Supported Devices

- Petkit W4X (Eversweet 3 Pro)
- Petkit W5 (Eversweet Mini) 
- Petkit W5C (Eversweet Mini)
- Petkit W5N (Eversweet Mini)
- Petkit CTW2 (Eversweet Solo 2)
- Petkit W4X UVC (Eversweet 3 Pro UVC)

## Installation

### Method 1: HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Petkit BLE" and install
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "Petkit BLE" and follow the setup wizard

### Method 2: Manual Installation

1. Copy the `custom_components/petkit_ble` folder to your Home Assistant `custom_components` directory
2. Ensure the `PetkitW5BLEMQTT` folder is also copied to the same location as the custom component
3. Restart Home Assistant
4. Add the integration via the UI

### File Structure
```
config/
├── custom_components/
│   └── petkit_ble/
│       ├── __init__.py
│       ├── binary_sensor.py
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── ha_bluetooth_adapter.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── services.yaml
│       ├── strings.json
│       └── switch.py
└── PetkitW5BLEMQTT/
    ├── __init__.py
    ├── ble_manager.py
    ├── commands.py
    ├── constants.py
    ├── device.py
    ├── event_handlers.py
    ├── logger.py
    ├── parsers.py
    ├── requirements.txt
    └── utils.py
```

## Configuration

### Prerequisites
- **Home Assistant Bluetooth**: Ensure Home Assistant has Bluetooth enabled and configured
- **Bluetooth Adapter**: USB Bluetooth dongle or built-in Bluetooth adapter
- **Device Proximity**: Petkit fountain within BLE range (~10m of your HA system)

### Automatic Discovery
Petkit devices are automatically discovered through Home Assistant's built-in Bluetooth integration and will appear in Settings → Devices & Services → Discovered when in range.

### Manual Setup
1. Navigate to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Petkit BLE Water Fountain" 
4. Select your device from Home Assistant's discovered BLE devices list
5. Complete the setup process

### Configuration Options
- **Device Address**: BLE MAC address of your fountain (auto-discovered via HA Bluetooth)
- **Update Interval**: 30 seconds (automatic device polling via Home Assistant's Bluetooth coordinator)
- **Shared Bluetooth Access**: Automatically handles multiple integrations using the same Bluetooth adapter

## Usage

### Basic Operations
- Use the **Power** switch to turn your fountain on/off
- Toggle **Smart Mode** to enable/disable intelligent operation scheduling
- Monitor filter status and replace when the **Filter** sensor shows low percentage

### Automation Examples

**Low Battery Alert:**
```yaml
automation:
  - alias: "Petkit Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.petkit_fountain_battery
        below: 20
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Petkit fountain battery is low ({{ states('sensor.petkit_fountain_battery') }}%)"
```

**Filter Replacement Reminder:**
```yaml
automation:
  - alias: "Petkit Filter Replacement"
    trigger:
      - platform: numeric_state
        entity_id: sensor.petkit_fountain_filter_time_left
        below: 3
    action:
      - service: persistent_notification.create
        data:
          title: "Petkit Filter Maintenance"
          message: "Replace fountain filter in {{ states('sensor.petkit_fountain_filter_time_left') }} days"
```

**Water Missing Alert:**
```yaml
automation:
  - alias: "Petkit Water Refill"
    trigger:
      - platform: state
        entity_id: binary_sensor.petkit_fountain_water_missing
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Petkit fountain needs water refill!"
```

## Troubleshooting

### Connection Issues
- Ensure your fountain is powered on and within BLE range (~10m)
- Check Home Assistant logs for BLE connectivity errors
- Restart the integration if connection is lost
- Verify Bluetooth is enabled on your Home Assistant host

### Performance Optimization
- Update interval is set to 30 seconds to balance data freshness with battery life
- Diagnostic entities (RSSI, voltage) are disabled by default to reduce clutter
- Device automatically reconnects if BLE connection is lost

### Known Limitations
- Only one Home Assistant instance can connect to a device at a time
- Using CMD 73 may interfere with the official Petkit app
- Do Not Disturb and LED scheduling features are not yet implemented
- Some advanced features may require device-specific testing

### Logging
Enable debug logging for troubleshooting:
```yaml
logger:
  default: info
  logs:
    custom_components.petkit_ble: debug
```

## Development

This integration uses the existing PetkitW5BLEMQTT library as-is, without modifications to the core BLE communication code. The Home Assistant integration layer provides proper Bluetooth sharing and management:

### Architecture Components
- **HA Bluetooth Adapter** (`ha_bluetooth_adapter.py`): Bridges Home Assistant's Bluetooth APIs with existing Petkit library
- **Active Bluetooth Coordinator** (`coordinator.py`): Uses ActiveBluetoothProcessorCoordinator for proper HA integration
- **Config Flow** (`config_flow.py`): Integrates with HA's Bluetooth discovery system
- **Entities**: Exposes device data as Home Assistant sensors/switches/binary sensors
- **Shared Bluetooth Access**: Properly coordinates with other HA integrations using the same Bluetooth adapter

### Key Integration Features
- **Home Assistant Bluetooth Integration**: Uses `homeassistant.components.bluetooth` APIs instead of direct `bleak` access
- **Shared Dongle Support**: Multiple integrations can safely share the same Bluetooth adapter
- **Automatic Discovery**: Integrates with HA's built-in Bluetooth discovery system
- **Connection Resilience**: Uses `bleak-retry-connector` for robust connections
- **Proper Cleanup**: Manages Bluetooth resources according to HA best practices

### Architecture Details
- `coordinator.py` - ActiveBluetoothProcessorCoordinator for HA Bluetooth integration
- `ha_bluetooth_adapter.py` - Adapter layer between HA Bluetooth APIs and existing Petkit library
- `config_flow.py` - HA Bluetooth discovery integration and device selection
- `sensor.py` - Device metrics as Home Assistant sensors  
- `switch.py` - Device controls as Home Assistant switches
- `binary_sensor.py` - Status indicators as binary sensors

## Contributing

Contributions are welcome! Please ensure:
- No modifications to the existing PetkitW5BLEMQTT library
- Follow Home Assistant development guidelines
- Test with real Petkit devices when possible
- Update documentation for new features

## License

This integration maintains the same license as the original PetkitW5BLEMQTT project.