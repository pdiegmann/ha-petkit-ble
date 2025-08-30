"""Petkit BLE Water Fountain integration for Home Assistant."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .coordinator import PetkitBLECoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR]

# Service schemas
SERVICE_RESET_FILTER = "reset_filter"
SERVICE_SET_DEVICE_CONFIG = "set_device_config"

SERVICE_RESET_FILTER_SCHEMA = vol.Schema({})

SERVICE_SET_DEVICE_CONFIG_SCHEMA = vol.Schema({
    vol.Optional("smart_time_on"): cv.positive_int,
    vol.Optional("smart_time_off"): cv.positive_int,
    vol.Optional("led_brightness", default=80): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Petkit BLE from a config entry."""
    coordinator = PetkitBLECoordinator(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Start the coordinator (this replaces async_config_entry_first_refresh for ActiveBluetoothProcessorCoordinator)
    entry.async_on_unload(coordinator.async_start())

    # Register services
    async def handle_reset_filter(call: ServiceCall) -> None:
        """Handle the reset filter service call."""
        await coordinator.async_reset_filter()
        await coordinator.async_request_refresh()

    async def handle_set_device_config(call: ServiceCall) -> None:
        """Handle the set device config service call."""
        # Build config data array based on current device config
        current_config = coordinator.device.config
        
        # Extract parameters with defaults from current config
        smart_time_on = call.data.get("smart_time_on", current_config.get("smart_time_on", 30))
        smart_time_off = call.data.get("smart_time_off", current_config.get("smart_time_off", 60))
        led_brightness = call.data.get("led_brightness", current_config.get("led_brightness", 80))
        
        # Build the configuration array (this matches the device's expected format)
        config_data = [
            smart_time_on,
            smart_time_off,
            current_config.get("led_switch", 1),
            led_brightness,
            current_config.get("led_on_byte1", 0),
            current_config.get("led_on_byte2", 0),
            current_config.get("led_off_byte1", 0),
            current_config.get("led_off_byte2", 0),
            current_config.get("do_not_disturb_switch", 0),
            current_config.get("dnd_on_byte1", 0),
            current_config.get("dnd_on_byte2", 0),
            current_config.get("dnd_off_byte1", 0),
            current_config.get("dnd_off_byte2", 0),
            current_config.get("is_locked", 0)
        ]
        
        await coordinator.async_set_device_config(config_data)
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_FILTER,
        handle_reset_filter,
        schema=SERVICE_RESET_FILTER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_DEVICE_CONFIG,
        handle_set_device_config,
        schema=SERVICE_SET_DEVICE_CONFIG_SCHEMA,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        # Remove services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_RESET_FILTER)
            hass.services.async_remove(DOMAIN, SERVICE_SET_DEVICE_CONFIG)

    return unload_ok