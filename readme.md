# Petkit BLE Water Fountain - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

A Home Assistant integration for controlling Petkit W5 series water fountains via Bluetooth Low Energy (BLE). Control your pet's water fountain locally without cloud dependencies.

## Features

- **Local Control**: No cloud connection required - all communication via BLE
- **Multiple Entity Types**: Sensors, switches, and binary sensors for complete device monitoring
- **Real-time Status**: Monitor battery, filter status, water levels, and more
- **Device Control**: 
  - Switch between Normal and Smart operating modes
  - Control LED brightness and on/off schedules
  - Manage Do Not Disturb functionality
  - Reset filter and monitor its lifetime
- **Home Assistant Services**: Advanced device configuration through HA services
- **Energy Monitoring**: Track power consumption and runtime statistics
- **Alerts**: Receive notifications for breakdowns, filter changes, and low water

## Supported Devices

- **Petkit W4 Series**
- **Petkit W5 Series** (Tested with Eversweet 2 Solo)
- **Petkit CTW2 Series**

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. In HACS, go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/pdiegmann/ha-petkit-ble`
5. Select "Integration" as the category
6. Click "Add"
7. Find "Petkit BLE Water Fountain" in the integration list and install it
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/petkit_ble` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration -> Integrations -> Add Integration
4. Search for "Petkit BLE" and follow the setup process

## Configuration

### Prerequisites

- Home Assistant 2023.8.0 or later
- Your Petkit device must be discoverable via Bluetooth
- Home Assistant must have Bluetooth access (built-in or USB adapter)

### Setup

1. Go to **Configuration** -> **Integrations**
2. Click **Add Integration**
3. Search for "**Petkit BLE Water Fountain**"
4. The integration will automatically discover available Petkit devices
5. Select your device from the list
6. Click **Submit** to complete the setup

The integration will create entities for:

#### Sensors
- Battery level
- Filter percentage remaining
- Filter time left
- Pump runtime (total and today)
- Purified water (total and today)
- Energy consumption
- RSSI (signal strength)
- Voltage

#### Binary Sensors
- Power status
- Running status
- Warning indicators (breakdown, filter, water missing)
- DND (Do Not Disturb) state
- Lock state

#### Switches
- Power on/off
- Smart mode toggle
- LED control

## Services

The integration provides Home Assistant services for advanced control:

### `petkit_ble.reset_filter`
Reset the water filter counter.

### `petkit_ble.set_device_config`
Configure device settings including:
- `smart_time_on`: Smart mode on duration (minutes)
- `smart_time_off`: Smart mode off duration (minutes)  
- `led_brightness`: LED brightness (0-100%)

Example service call:
```yaml
service: petkit_ble.set_device_config
data:
  smart_time_on: 30
  smart_time_off: 90
  led_brightness: 50
```

## Automation Examples

### Low Battery Alert
```yaml
automation:
  - alias: "Petkit Low Battery Alert"
    trigger:
      platform: numeric_state
      entity_id: sensor.petkit_water_fountain_battery
      below: 20
    action:
      service: notify.mobile_app
      data:
        message: "Water fountain battery is low ({{ states('sensor.petkit_water_fountain_battery') }}%)"
```

### Filter Replacement Reminder
```yaml
automation:
  - alias: "Petkit Filter Replacement"
    trigger:
      platform: numeric_state
      entity_id: sensor.petkit_water_fountain_filter_percentage
      below: 10
    action:
      service: notify.mobile_app
      data:
        message: "Time to replace the water fountain filter ({{ states('sensor.petkit_water_fountain_filter_percentage') }}% remaining)"
```

## Troubleshooting

### Device Not Found
- Ensure your Petkit device is in pairing mode
- Check that Bluetooth is enabled on your Home Assistant host
- Move Home Assistant closer to the device during setup
- Restart the Bluetooth service: `sudo systemctl restart bluetooth`

### Connection Issues
- The device can only maintain one BLE connection at a time
- Close the official Petkit app before using this integration
- Using certain commands may interfere with the official app's communication

### Debug Logging
Enable debug logging by adding to your `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.petkit_ble: debug
```

## Known Limitations

- Device can only maintain one active BLE connection
- Do Not Disturb scheduling not yet fully supported
- Some advanced LED scheduling features not implemented
- Using the integration alongside the official app may cause conflicts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you find this integration useful, consider supporting the development:

[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)][buymecoffee]

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Inspired by [RobertD502's Petkit integration](https://github.com/RobertD502/homeassistant-petkit)
- Based on [petkitaio library](https://github.com/RobertD502/petkitaio)
- BLE protocol analysis from [PetKit Eversweet Pro 3 research](https://colab.research.google.com/drive/1gWwLz1Wi_WujvvSaTJpPMW5i3YideSAb)

---

[buymecoffee]: https://www.buymeacoffee.com/pdiegmann
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/pdiegmann/ha-petkit-ble.svg?style=for-the-badge
[commits]: https://github.com/pdiegmann/ha-petkit-ble/commits/main
[license-shield]: https://img.shields.io/github/license/pdiegmann/ha-petkit-ble.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40pdiegmann-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pdiegmann/ha-petkit-ble.svg?style=for-the-badge
[releases]: https://github.com/pdiegmann/ha-petkit-ble/releases