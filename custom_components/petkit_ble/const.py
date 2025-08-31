"""Constants for the Petkit BLE integration."""

DOMAIN = "petkit_ble"

# Configuration keys
CONF_ADDRESS = "address"
CONF_UPDATE_INTERVAL = "update_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_UPDATE_INTERVAL = 10  # seconds
HEARTBEAT_INTERVAL = 60     # seconds

# Device types
SUPPORTED_DEVICES = ["W4", "W5", "CTW2"]

# Entity attributes
ATTR_BATTERY = "battery"
ATTR_FILTER_PERCENTAGE = "filter_percentage"
ATTR_FILTER_TIME_LEFT = "filter_time_left"
ATTR_PUMP_RUNTIME = "pump_runtime"
ATTR_PUMP_RUNTIME_TODAY = "pump_runtime_today"
ATTR_PURIFIED_WATER = "purified_water"
ATTR_PURIFIED_WATER_TODAY = "purified_water_today"
ATTR_ENERGY_CONSUMED = "energy_consumed"
ATTR_RSSI = "rssi"
ATTR_VOLTAGE = "voltage"
ATTR_MODE = "mode"
ATTR_POWER_STATUS = "power_status"
ATTR_RUNNING_STATUS = "running_status"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_LED_SWITCH = "led_switch"
ATTR_DND_STATE = "dnd_state"
ATTR_IS_LOCKED = "is_locked"

# Warning attributes
ATTR_WARNING_BREAKDOWN = "warning_breakdown"
ATTR_WARNING_FILTER = "warning_filter"
ATTR_WARNING_WATER_MISSING = "warning_water_missing"

# Device modes
MODE_NORMAL = 1
MODE_SMART = 2

# Power states
POWER_OFF = 0
POWER_ON = 1