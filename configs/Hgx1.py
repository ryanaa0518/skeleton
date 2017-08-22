#! /usr/bin/python

HOME_PATH = './'
CACHE_PATH = '/var/cache/obmc/'
FLASH_DOWNLOAD_PATH = "/tmp"
GPIO_BASE = 320
SYSTEM_NAME = "Hgx1"


## System states
##   state can change to next state in 2 ways:
##   - a process emits a GotoSystemState signal with state name to goto
##   - objects specified in EXIT_STATE_DEPEND have started
SYSTEM_STATES = [
	'BASE_APPS',
	'BMC_STARTING',
	'BMC_STARTING2',
	'BMC_READY',
	'HOST_POWERING_ON',
	'HOST_POWERED_ON',
	'INVENTORY_UPLOADED',
	'HOST_BOOTING',
	'HOST_BOOTED',
	'HOST_POWERED_OFF',
]

EXIT_STATE_DEPEND = {
	'BASE_APPS' : {
		'/org/openbmc/sensors': 0,
	},
	'BMC_STARTING' : {
#		'/org/openbmc/control/power0' : 0,
#		'/org/openbmc/control/host0' : 0,
#		'/org/openbmc/control/flash/bios' : 0,
#		'/org/openbmc/sensors/speed/fan5': 0,
#		'/org/openbmc/inventory/system/chassis/io_board' : 0,
	},
	'BMC_STARTING2' : {
#		'/org/openbmc/control/fans' : 0,
#		'/org/openbmc/control/chassis0': 0,
	},
}

## method will be called when state is entered
ENTER_STATE_CALLBACK = {
	'INVENTORY_UPLOADED' : {
		'boot' : {
			'bus_name'    : 'org.openbmc.control.Host',
			'obj_name'    : '/org/openbmc/control/host0',
			'interface_name' : 'org.openbmc.control.Host',
		},
		'setOn' : {
			'bus_name'   : 'org.openbmc.control.led',
			'obj_name'   : '/org/openbmc/control/led/identify',
			'interface_name' : 'org.openbmc.Led',
		}
	},
	'HOST_POWERED_OFF' : {
		'setOff' : {
			'bus_name'   : 'org.openbmc.control.led',
			'obj_name'   : '/org/openbmc/control/led/identify',
			'interface_name' : 'org.openbmc.Led',
		}

	},
	'BMC_READY' : {
		'setBlinkSlow' : {
			'bus_name'   : 'org.openbmc.control.led',
			'obj_name'   : '/org/openbmc/control/led/heartbeat',
			'interface_name' : 'org.openbmc.Led',
		},
		'init' : {
			'bus_name'   : 'org.openbmc.control.Flash',
			'obj_name'   : '/org/openbmc/control/flash/bios',
			'interface_name' : 'org.openbmc.Flash',
		}
	}
}

APPS = {
	'startup_hacks' : {
		'system_state'    : 'BASE_APPS',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'startup_hacks.sh',
	},
	'inventory' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'inventory_items.py',
		'args'            : [ SYSTEM_NAME ]
	},
	'inventory_upload' : {
		'system_state'    : 'HOST_POWERED_ON',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'goto_system_state.py',
		'args'            : [ 'INVENTORY_UPLOADED', 'inventory_upload.py' ]
	},
	'pcie_present' : {
		'system_state'    : 'INVENTORY_UPLOADED',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'pcie_slot_present.exe',
	},
	'fan_control' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'fan_control.py',
	},
	'hwmon' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'hwmon.py',
		'args'            : [ SYSTEM_NAME ]
	},
	'sensor_manager' : {
		'system_state'    : 'BASE_APPS',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'sensor_manager2.py',
		'args'            : [ SYSTEM_NAME ]
	},
	'host_watchdog' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'host_watchdog.exe',
	},
	'power_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name' : 'power_control.exe',
		'args' : [ '3000', '10' ]
	},
	'power_button' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'button_power.exe',
	},
        'reset_button' : {
                'system_state'    : 'BMC_STARTING',
                'start_process'   : True,
                'monitor_process' : True,
                'process_name'    : 'button_reset.exe',
        },
	'host_checkstop' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'host_checkstop.exe',
	},
	'led_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'led_controller.exe',
	},
	'flash_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'flash_bios.exe',
	},
	'bmc_flash_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'bmc_update.py',
	},
	'download_manager' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'download_manager.py',
		'args'            : [ SYSTEM_NAME ]
	},
	'host_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'control_host.exe',
	},
	'chassis_control' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'chassis_control.py',
	},
	'board_vpd' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'phosphor-read-eeprom',
		'args'            : ['--eeprom','/sys/bus/i2c/devices/0-0050/eeprom','--fruid','64'],
	},
	'motherboard_vpd' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'phosphor-read-eeprom',
		'args'            : ['--eeprom','/sys/bus/i2c/devices/4-0054/eeprom','--fruid','3'],
	},
	'exp_vpd' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'phosphor-read-eeprom',
		'args'            : ['--eeprom','/sys/bus/i2c/devices/6-0051/eeprom','--fruid','65'],
	},
	'hdd_vpd' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'phosphor-read-eeprom',
		'args'            : ['--eeprom','/sys/bus/i2c/devices/6-0055/eeprom','--fruid','66'],
	},
	'restore' : {
		'system_state'    : 'BMC_READY',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'discover_system_state.py',
	},
	'info' : {
                'system_state'    : 'BMC_STARTING2',
                'start_process'   : True,
                'monitor_process' : True,
                'process_name'    : 'info.exe',
	},
	'fan_algorithm' : {
                'system_state'    : 'BMC_READY',
                'start_process'   : True,
                'monitor_process' : True,
                'process_name'    : 'fan_algorithm.exe',
	},
	'bmc_control' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'control_bmc.exe',
	},
	'id_button' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'button_id.exe',
	},
	'cable_led' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'cable_led.exe',
	},
}

CACHED_INTERFACES = {
		"org.openbmc.InventoryItem" : True,
		"org.openbmc.control.Chassis" : True,
	}
INVENTORY_ROOT = '/org/openbmc/inventory'

FRU_INSTANCES = {
	        '<inventory_root>/system' : { 'fru_type' : 'SYSTEM','is_fru' : True, 'present' : "True" },
        	'<inventory_root>/system/misc' : { 'fru_type' : 'SYSTEM','is_fru' : False, },

        	'<inventory_root>/system/chassis' : { 'fru_type' : 'SYSTEM','is_fru' : True, 'present' : "True" },

	        '<inventory_root>/system/chassis/motherboard' : { 'fru_type' : 'MAIN_PLANAR','is_fru' : True, },

        	'<inventory_root>/system/systemevent'                  : { 'fru_type' : 'SYSTEM_EVENT', 'is_fru' : False, },
        	'<inventory_root>/system/chassis/motherboard/refclock' : { 'fru_type' : 'MAIN_PLANAR', 'is_fru' : False, },
        	'<inventory_root>/system/chassis/motherboard/pcieclock': { 'fru_type' : 'MAIN_PLANAR', 'is_fru' : False, },
        	'<inventory_root>/system/chassis/motherboard/todclock' : { 'fru_type' : 'MAIN_PLANAR', 'is_fru' : False, },
        	'<inventory_root>/system/chassis/motherboard/apss'     : { 'fru_type' : 'MAIN_PLANAR', 'is_fru' : False, },
	
	        '<inventory_root>/system/chassis/motherboard/bmc' : { 'fru_type' : 'BMC','is_fru' : False, 'manufacturer' : 'ASPEED' },
}

ID_LOOKUP = {
	'FRU' : {
	},
	'FRU_STR' : {
	},
	'SENSOR' : {
	},
	'GPIO_PRESENT' : {
	}
}

GPIO_CONFIG = {}
GPIO_CONFIG['POWER_BUTTON'] = { 'gpio_pin': 'F1', 'direction': 'both' }
GPIO_CONFIG['IDBTN']       = { 'gpio_pin': 'F3', 'direction': 'both' }

def convertGpio(name):
	name = name.upper()
	c = name[0:1]
	offset = int(name[1:])
	a = ord(c)-65
	base = a*8+GPIO_BASE
	return base+offset

HWMON_CONFIG = {
	'11-0048' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP1','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-0049' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP2','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004a' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP3','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004b' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP4','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004c' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP5','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004d' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP6','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004e' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP7','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
	'11-004f' :  {
		'names' : {
			'temp1_input' : { 'object_path' : 'temperature/TMP8','poll_interval' : 5000,'scale' : 1000,'units' : 'C',
					'critical_upper' : 40, 'critical_lower' : -100, 'warning_upper' : 36, 'warning_lower' : -99, 'emergency_enabled' : True },
		}
	},
}

# Miscellaneous non-poll sensor with system specific properties.
# The sensor id is the same as those defined in ID_LOOKUP['SENSOR'].
MISC_SENSORS = {
}
