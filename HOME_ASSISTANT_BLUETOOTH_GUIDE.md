# Home Assistant Bluetooth Integration Guidelines

This document provides comprehensive guidance for writing **custom Home Assistant integrations** that use Bluetooth (via a USB dongle or onboard adapter). It merges best practices from the official Home Assistant developer docs with additional context, ensuring integrations use Bluetooth **correctly and cooperatively** within Home Assistant.

---

## 🔑 Core Principles

1. **Never talk to the dongle directly.**

   * Do **not** access `/dev/hciX`, `/dev/ttyUSBX`, or raw HCI sockets.
   * Do **not** use external libraries like `pybluez`, `bluepy`, or standalone `bleak` scanners.
   * Instead, always go through Home Assistant’s built-in `bluetooth` integration.

2. **Home Assistant owns the adapters.**

   * HA runs a background scanner that manages all connected Bluetooth adapters (dongles, onboard controllers, remotes/proxies).
   * Multiple integrations can safely share the same dongle.

3. **Integrations consume from the shared Bluetooth API.**

   * The `bluetooth` integration multiplexes advertisement scanning and connection handling.
   * Your integration subscribes to discovery events and requests connections via HA’s helpers.

4. **Use `bluetooth_adapters` in `manifest.json`.**

   * Add `"dependencies": ["bluetooth_adapters"]` to ensure remote adapters are available before setup.

---

## ✅ Correct APIs and Patterns

### Discovery & Advertisement Listening

```python
from homeassistant.components import bluetooth

@callback
def _async_discovered_device(service_info: bluetooth.BluetoothServiceInfoBleak, change: bluetooth.BluetoothChange):
    _LOGGER.info("Discovered %s RSSI=%s", service_info.address, service_info.rssi)

entry.async_on_unload(
    bluetooth.async_register_callback(
        hass,
        _async_discovered_device,
        {"address": "44:33:11:22:33:22"},  # matchers can use address, UUID, manufacturer ID, etc.
        bluetooth.BluetoothScanningMode.ACTIVE,
    )
)
```

### Device Lookup

```python
ble_device = bluetooth.async_ble_device_from_address(hass, "AA:BB:CC:DD:EE:FF", connectable=True)
if ble_device:
    # Use with a BluetoothClient
    pass
```

### Connections

```python
from homeassistant.components.bluetooth import BluetoothClient

async with BluetoothClient(ble_device, "my_integration") as client:
    await client.connect()
    services = await client.get_services()
```

### Shared Scanner Access

```python
scanner = bluetooth.async_get_scanner(hass)
```

### Unavailability Tracking

```python
def _unavailable_callback(info: bluetooth.BluetoothServiceInfoBleak):
    _LOGGER.debug("%s is no longer seen", info.address)

cancel = bluetooth.async_track_unavailable(hass, _unavailable_callback, "44:44:33:11:23:42", connectable=True)
```

### Advertisement Processing

```python
service_info = await bluetooth.async_process_advertisements(
    hass,
    lambda si: 323 in si.manufacturer_data,
    {"address": "AA:BB:CC:DD:EE:FF", "connectable": False},
    bluetooth.BluetoothScanningMode.ACTIVE,
    timeout=30,
)
```

### Rediscovery

```python
bluetooth.async_rediscover_address(hass, "44:44:33:11:23:42")
```

---

## ⚙️ Coordinators for Common Patterns

### PassiveBluetoothProcessorCoordinator

* For devices updating **only via advertisements** (sensors, binary sensors, events).

```python
from homeassistant.components.bluetooth.passive_update_processor import PassiveBluetoothProcessorCoordinator

coordinator = PassiveBluetoothProcessorCoordinator(
    hass,
    _LOGGER,
    address=address,
    mode=bluetooth.BluetoothScanningMode.ACTIVE,
    update_method=data.update,
)
```

### ActiveBluetoothProcessorCoordinator

* For devices needing **both advertisements and active connections**.

```python
from homeassistant.components.bluetooth.active_update_processor import ActiveBluetoothProcessorCoordinator

coordinator = ActiveBluetoothProcessorCoordinator(
    hass,
    _LOGGER,
    address=address,
    mode=bluetooth.BluetoothScanningMode.PASSIVE,
    update_method=data.update,
    needs_poll_method=_needs_poll,
    poll_method=_async_poll,
    connectable=False,
)
```

### Passive/Active BluetoothDataUpdateCoordinator

* Similar to DataUpdateCoordinator, but driven by advertisements.

---

## 📚 Best Practices

* **Do not reuse `BleakClient`** between connections — create new clients per connection attempt.
* **Use ≥10s connection timeouts** — BlueZ requires time to resolve services.
* **Expect transient connection failures** — retry is normal. Use [`bleak-retry-connector`](https://pypi.org/project/bleak-retry-connector/) for resilience.
* **Differentiate connectable vs non-connectable controllers.**

  * If a device doesn’t require connections, set `connectable=False` to allow non-connectable adapters to contribute.
* **Always respect HA’s learned advertising intervals** when tracking availability.

---

## 🚫 What Not To Do

* ❌ **Do not** open `/dev/hciX` directly.
* ❌ **Do not** run your own scanner loop.
* ❌ **Do not** assume a fixed adapter (`hci0`, `hci1`).
* ❌ **Do not** bypass HA’s Bluetooth integration.

---

## 🔄 Multi-Dongle Handling

* HA supports multiple adapters simultaneously.
* Adapter routing is handled internally; integrations should remain agnostic.
* If multiple adapters can reach a device, HA selects the best (RSSI, connectable status).

---

## 📚 API Summary Cheat Sheet

* `async_register_callback` → Subscribe to advertisements.
* `async_get_scanner` → Get shared scanner.
* `async_scanner_count` → See if scanners exist.
* `async_ble_device_from_address` → Get BLEDevice for connection.
* `async_last_service_info` → Latest advertisement.
* `async_address_present` → Is device still present?
* `async_discovered_service_info` → List current discoveries.
* `async_scanner_devices_by_address` → Per-adapter device view.
* `async_track_unavailable` → Track device disappearance.
* `async_get_learned_advertising_interval` → Retrieve learned advertising interval.
* `async_set_fallback_availability_interval` → Override fallback interval.
* `async_process_advertisements` → Wait for specific advertisements.
* `async_rediscover_address` → Trigger rediscovery.
* `async_register_scanner` → Register external scanner.
* `async_remove_scanner` → Remove external scanner.

---

## 📝 Summary for Coding Agents

* Always use `homeassistant.components.bluetooth` APIs.
* Add `bluetooth_adapters` dependency in `manifest.json`.
* Use coordinators (`PassiveBluetoothProcessorCoordinator`, `ActiveBluetoothProcessorCoordinator`) where possible.
* Avoid raw dongle access, direct BlueZ connections, or custom scanners.
* Handle connection retries, timeouts, and connectable/non-connectable controllers correctly.
* Assume multiple adapters — never hardcode.

By following these rules and APIs, your integration will **share the Bluetooth dongle correctly** with Home Assistant and other integrations.

