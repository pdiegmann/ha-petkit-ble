from .utils import Utils

class Parsers:
    # Get Battery Synchronization
    @staticmethod
    def device_battery(data, alias):
        return {
            "voltage": ((data[0] * 16 * 16) + (data[1] & 255)) / 1000.0,  # Magic borrowed from Petkit
            "battery": data[2]
        }

    # Init data
    @staticmethod
    def device_init(data, alias):
        return {"serial": Utils.bytes_to_long(data[7:11])}

    # Synchronize data
    @staticmethod
    def device_synchronization(data, alias):
        return {"device_initialized": data[0]}

    # Device Information
    @staticmethod
    def device_firmware(data, alias):
        # Extract the firmware version - supposedly
        # According to the com.petkit.oversea app, the Hardware is actually [0] while firmware is [1]
        # they are however presented as v[0].[1] in the actual app
        firmware = float(f"{data[0]}.{data[1]}")
        
        return {"firmware": firmware }
        
    # Get device state
    @staticmethod
    def device_state(data, alias):
        return {
            "power_status": data[0],
            "mode": data[1],
            "dnd_state": data[2],
            "warning_breakdown": data[3],
            "warning_water_missing": data[4],
            "warning_filter": data[5],
            "pump_runtime": Utils.bytes_to_integer(data[6:10]),
            "filter_percentage": Utils.byte_to_integer(data[10]) / 100,
            "running_status": Utils.byte_to_integer(data[11]),
        }

    # Get device configuration
    @staticmethod
    def device_configuration(data, alias):
        led_light_time_on = Utils.bytes_to_short(data[4:6])
        led_light_time_off = Utils.bytes_to_short(data[6:8])
        do_not_disturb_time_on = Utils.bytes_to_short(data[9:11])
        do_not_disturb_time_off = Utils.bytes_to_short(data[11:13])
    
        return {
            "smart_time_on": data[0],
            "smart_time_off": data[1],
            "led_switch": data[2],
            "led_brightness": data[3],
            "led_light_time_on": led_light_time_on,
            "led_light_time_on_readable": Utils.minutes_to_timestamp(led_light_time_on),
            "led_on_byte1": data[4],
            "led_on_byte2": data[5],
            "led_light_time_off": led_light_time_off,
            "led_light_time_off_readable": Utils.minutes_to_timestamp(led_light_time_off),
            "led_off_byte1": data[6],
            "led_off_byte2": data[7],
            "do_not_disturb_switch": data[8],
            "do_not_disturb_time_on": do_not_disturb_time_on,
            "do_not_disturb_time_on_readable": Utils.minutes_to_timestamp(do_not_disturb_time_on),
            "dnd_on_byte1": data[9],
            "dnd_on_byte2": data[10],
            "do_not_disturb_time_off": do_not_disturb_time_off,
            "do_not_disturb_time_off_readable": Utils.minutes_to_timestamp(do_not_disturb_time_off),
            "dnd_off_byte1": data[11],
            "dnd_off_byte2": data[12],
            "is_locked": data[13],
        }
        
    # Get device ID and serial
    @staticmethod
    def device_identifiers(data, alias):
        device_id_bytes, device_id = Utils.extract_device_id(data)
        serial = Utils.extract_serial_number(data)
        
        return {
            "device_id": device_id,
            "device_id_bytes": device_id_bytes,
            "serial": serial,
        }

    # Status
    @staticmethod
    def device_status(data, alias):
        mode = data[1]
        filter_percentage = Utils.byte_to_integer(data[10]) / 100
        smart_time_on = data[16]
        smart_time_off = data[17]
        alias = alias
        pump_runtime_today = Utils.bytes_to_integer(data[12:16])
        pump_runtime = Utils.bytes_to_integer(data[6:10])
        
        filter_time_left, purified_water, purified_water_today, energy_consumed = Utils.calculate_values(mode, filter_percentage, smart_time_on, smart_time_off, alias, pump_runtime_today, pump_runtime)
        
        led_light_time_on = Utils.bytes_to_short(data[20:22])
        led_light_time_off = Utils.bytes_to_short(data[22:24])
        do_not_disturb_time_on = Utils.bytes_to_short(data[25:27])
        do_not_disturb_time_off = Utils.bytes_to_short(data[27:29])
        
        return {
            "power_status": data[0],
            "mode": mode,
            "dnd_state": data[2],
            "warning_breakdown": data[3],
            "warning_water_missing": data[4],
            "warning_filter": data[5],
            "pump_runtime": pump_runtime,
            "filter_percentage": filter_percentage,
            "running_status": Utils.byte_to_integer(data[11]),
            "pump_runtime_today": pump_runtime_today,
            "smart_time_on": smart_time_on,
            "smart_time_off": smart_time_off,
            "led_switch": data[18],
            "led_brightness": data[19],
            "led_light_time_on": led_light_time_on,
            "led_light_time_on_readable": Utils.minutes_to_timestamp(led_light_time_on),
            "led_on_byte1": data[20],
            "led_on_byte2": data[21],
            "led_light_time_off": led_light_time_off,
            "led_light_time_off_readable": Utils.minutes_to_timestamp(led_light_time_off),
            "led_off_byte1": data[22],
            "led_off_byte2": data[23],
            "do_not_disturb_switch": data[24],
            "do_not_disturb_time_on": do_not_disturb_time_on,
            "do_not_disturb_time_on_readable": Utils.minutes_to_timestamp(do_not_disturb_time_on),
            "dnd_on_byte1": data[25],
            "dnd_on_byte2": data[26],
            "do_not_disturb_time_off": do_not_disturb_time_off,
            "do_not_disturb_time_off_readable": Utils.minutes_to_timestamp(do_not_disturb_time_off),
            "dnd_off_byte1": data[27],
            "dnd_off_byte2": data[28],
            "pump_runtime_readable": Utils.get_timestamp_days(pump_runtime),
            "pump_runtime_today_readable": Utils.get_timestamp_hours(pump_runtime_today),
            "filter_time_left": filter_time_left,
            "purified_water": purified_water,
            "purified_water_today": purified_water_today,
            "energy_consumed": energy_consumed,
        }