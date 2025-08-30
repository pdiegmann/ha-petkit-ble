"""Config flow for Petkit BLE integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN, SUPPORTED_DEVICES

_LOGGER = logging.getLogger(__name__)

class PetkitBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Petkit BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, bluetooth.BluetoothServiceInfoBleak] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(format_mac(address))
            self._abort_if_unique_id_configured()

            # Test connection if possible, but allow configuration even if test fails
            connection_tested = await self._test_connection(address)
            if not connection_tested:
                _LOGGER.warning(
                    f"Could not verify connection to {address}, but allowing configuration. "
                    "Device may not be in range or powered on."
                )
            
            return self.async_create_entry(
                title=f"Petkit Water Fountain ({address})",
                data={CONF_ADDRESS: address},
            )

        # Get devices from HA's bluetooth discovery
        discovered_devices = await self._get_discovered_devices()
        
        if not discovered_devices:
            return self.async_abort(reason="no_devices_found")

        # Create the selection schema
        device_options = {
            address: f"{service_info.name} ({address})"
            for address, service_info in discovered_devices.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(device_options),
                }
            ),
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        device_name = discovery_info.name
        address = discovery_info.address
        
        # Check if this is a supported Petkit device
        if not device_name or not any(
            supported in device_name for supported in SUPPORTED_DEVICES
        ):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(format_mac(address))
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": device_name,
            "address": address,
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm bluetooth discovery."""
        if user_input is not None:
            address = self.context["title_placeholders"]["address"]
            
            # Test connection if possible, but allow configuration even if test fails
            connection_tested = await self._test_connection(address)
            if not connection_tested:
                _LOGGER.warning(
                    f"Could not verify connection to {address}, but allowing configuration. "
                    "Device may not be in range or powered on."
                )
            
            return self.async_create_entry(
                title=f"Petkit Water Fountain ({address})",
                data={CONF_ADDRESS: address},
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def _get_discovered_devices(self) -> dict[str, bluetooth.BluetoothServiceInfoBleak]:
        """Get Petkit devices from HA's bluetooth discovery."""
        try:
            # Use HA's bluetooth discovery instead of custom scanning
            discovered_devices = bluetooth.async_discovered_service_info(self.hass)
            
            # Filter for supported Petkit devices
            petkit_devices = {}
            for service_info in discovered_devices:
                if (service_info.name and 
                    any(device_type in service_info.name for device_type in SUPPORTED_DEVICES)):
                    petkit_devices[service_info.address] = service_info
                    _LOGGER.info(f"Found Petkit device: {service_info.name} ({service_info.address})")
            
            return petkit_devices
            
        except Exception as err:
            _LOGGER.error("Error getting discovered devices: %s", err)
            return {}

    async def _test_connection(self, address: str) -> bool:
        """Test if we can connect to the device using HA's bluetooth."""
        try:
            # Check if device is present in HA's bluetooth discovery
            if not bluetooth.async_address_present(self.hass, address, connectable=True):
                _LOGGER.error(f"Device {address} not present in HA bluetooth")
                return False
            
            # Get BLE device from HA's bluetooth integration
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, address, connectable=True
            )
            
            if not ble_device:
                _LOGGER.error(f"Device {address} not found in HA bluetooth")
                return False
            
            # Device is discoverable and has a BLE device object, consider it connectable
            _LOGGER.info(f"Device {address} is available for connection")
            return True
            
        except Exception as err:
            _LOGGER.error("Error testing connection to %s: %s", address, err)
            return False