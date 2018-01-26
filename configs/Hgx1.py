#! /usr/bin/python

from os.path import join
from glob import glob

HOME_PATH = './'
CACHE_PATH = '/var/cache/obmc/'
FLASH_DOWNLOAD_PATH = "/tmp"
GPIO_BASE = 320
SYSTEM_NAME = "Hgx1"

def find_gpio_base(path="/sys/class/gpio/"):
    pattern = "gpiochip*"
    for gc in glob(join(path, pattern)):
        with open(join(gc, "label")) as f:
            label = f.readline().strip()
        if label == "1e780000.gpio":
            with open(join(gc, "base")) as f:
                return int(f.readline().strip())
    # trigger a file not found exception
    open(join(path, "gpiochip"))

GPIO_BASE = find_gpio_base()

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
	'HOST_BOOTING',
	'HOST_BOOTED',
	'HOST_POWERED_OFF',
]

EXIT_STATE_DEPEND = {
	'BASE_APPS' : {
		'/org/openbmc/sensors': 0,
	},
	'BMC_STARTING' : {
		'/org/openbmc/inventory/system/chassis/io_board' : 0,
	},
	'BMC_STARTING2' : {
		'/org/openbmc/control/chassis0': 0,
	},
}

## method will be called when state is entered
ENTER_STATE_CALLBACK = {
	'BMC_READY' : {
		'setBlinkSlow' : {
			'bus_name'   : 'org.openbmc.control.led',
			'obj_name'   : '/org/openbmc/control/led/heartbeat',
			'interface_name' : 'org.openbmc.Led',
		},
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
		'process_name' : 'power_control_sthelens.exe',
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
	#'cable_led' : {
	#	'system_state'    : 'BMC_STARTING',
	#	'start_process'   : True,
	#	'monitor_process' : True,
	#	'process_name'    : 'cable_led.exe',
	#},
	'netman' : {
		'system_state'    : 'BMC_STARTING2',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'netman.py',
	},
	'sync_mac' : {
		'system_state'    : 'BMC_READY',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'sync_inventory_items.py',
		'args'            : ['-t','DAUGHTER_CARD','-n','io_board','-p','Custom Field 2','-s','mac'],
    },
	'fan_ctl' : {
		'system_state'    : 'BMC_STARTING',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'fan_generic_obj.exe',
	},
	'gpu_core' : {
		'system_state'    : 'BMC_READY',
		'start_process'   : True,
		'monitor_process' : True,
		'process_name'    : 'gpu_core.exe',
	},
	'node_init_sthelens' : {
		'system_state'    : 'BASE_APPS',
		'start_process'   : True,
		'monitor_process' : False,
		'process_name'    : 'node_init_sthelens.exe',
	},
	'pex_service' : {
                'system_state'    : 'BMC_READY',
                'start_process'   : True,
                'monitor_process' : True,
                'process_name'    : 'pex_core.exe',
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
	        '<inventory_root>/system/chassis/io_board' : { 'fru_type' : 'DAUGHTER_CARD','is_fru' : True,'Custom Field 2': '00:00:00:00:00:00',},
}

ID_LOOKUP = {
	'FRU' : {
		0x40 : '<inventory_root>/system/chassis/io_board',
	},
	'FRU_STR' : {
		'BOARD_100'  : '<inventory_root>/system/chassis/io_board',
	},
	'SENSOR' : {
	},
	'GPIO_PRESENT' : {
	}
}

GPIO_CONFIG = {}
GPIO_CONFIG['POWER_BUTTON'] = { 'gpio_pin': 'F1', 'direction': 'both' }
GPIO_CONFIG['IDBTN']       = { 'gpio_pin': 'F3', 'direction': 'both' }
GPIO_CONFIG['PGOOD'] = { 'gpio_pin': 'M2', 'direction': 'in', 'inverse': 'yes' }
GPIO_CONFIG['POWER_PIN'] = { 'gpio_pin': 'M3', 'direction': 'out' }
GPIO_CONFIG['POWER_STATE_LED'] = { 'gpio_pin': 'F2', 'direction': 'out', 'inverse': 'yes' }

def convertGpio(name):
    offset = int(filter(str.isdigit, name))
    port = filter(str.isalpha, name.upper())
    a = ord(port[-1]) - ord('A')
    if len(port) > 1:
        a += 26
    base = a * 8 + GPIO_BASE
    return base + offset

SENSOR_MONITOR_CONFIG = [
	['/org/openbmc/sensors/temperature/TMP9', { 
							'object_path' : '/sys/class/hwmon/hwmon1/temp1_input',
							'poll_interval' : 5000,
							'scale' : 1000,
							'units' : 'C',
							'critical_upper' : 37,
							'sensornumber' : '0x05',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'FIO Inlet 1 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/temperature/TMP10', {
							'object_path' : '/sys/class/hwmon/hwmon2/temp1_input',
							'poll_interval' : 5000,
							'scale' : 1000,
							'units' : 'C',
							'critical_upper' : 37,
							'sensornumber' : '0x06',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'FIO Inlet 2 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu1_temp', { 
							'object_path' : '/tmp/gpu/gpu1_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x41',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU1 Temp',
							'reading_error_count' : 0
						}
	],	
	['/org/openbmc/sensors/gpu/gpu2_temp', {
							'object_path' : '/tmp/gpu/gpu2_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x42',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU2 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu3_temp', { 
							'object_path' : '/tmp/gpu/gpu3_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x43',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU3 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu4_temp', { 
							'object_path' : '/tmp/gpu/gpu4_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x44',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU4 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu5_temp', {
							'object_path' : '/tmp/gpu/gpu5_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x45',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU5 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu6_temp', {
							'object_path' : '/tmp/gpu/gpu6_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x46',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU6 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu7_temp', { 
							'object_path' : '/tmp/gpu/gpu7_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x47',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU7 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu8_temp', { 
							'object_path' : '/tmp/gpu/gpu8_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 81,
							'sensornumber' : '0x48',
							'sensor_type': '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU8 Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/control/fan/fan1', { 
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm1_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0x1D',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'PWM 1',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/control/fan/fan2', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm2_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0X1E',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'PWM 2',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/control/fan/fan3', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm3_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0x1F',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name':'PWM 3',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/control/fan/fan4', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm4_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0x20',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'PWM 4',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/control/fan/fan5', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm5_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0x21',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'PWM 5',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/control/fan/fan6', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/pwm6_falling',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : '%',
							'critical_lower' : 18,
							'sensornumber' : '0x22',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'PWM 6',
							'reading_error_count' : 'N/A'
					}
	],
	['/org/openbmc/sensors/fan/fan_tacho1', { 
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho1_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x11',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 1',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho2', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho2_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x12',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 2',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho3', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho3_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x13',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 3',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho4', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho4_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x14',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 4',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho5', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho5_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x15',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 5',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho6', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho6_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x16',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 6',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho7', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho7_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x17',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 7',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho8', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho8_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x18',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 8',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho9', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho9_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x19',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 9',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho10', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho10_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x1A',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 10',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho11', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho11_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x1B',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 11',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/fan/fan_tacho12', {
							'object_path' : '/sys/devices/platform/ast_pwm_tacho.0/tacho12_rpm',
							'poll_interval' : 10000,
							'scale' : 1,
							'units' : 'rpm',
							'critical_lower' : 3800,
							'sensornumber' : '0x1C',
							'sensor_type' : '0x04',
							'reading_type' : '0x01',
							'sensor_name' : 'Fan Tach 12',
							'reading_error_count' : 'N/A'
						}
	],
	['/org/openbmc/sensors/pmbus/pmbus01/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon12/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x50',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU1 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus01/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon12/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x51',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU1 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus01/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon12/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x52',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU1 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus02/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon13/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x53',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU2 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus02/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon13/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x54',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU2 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus02/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon13/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x55',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU2 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus03/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon14/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x56',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU3 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus03/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon14/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x57',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU3 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus03/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon14/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x58',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU3 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus04/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon15/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x59',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU4 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus04/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon15/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x5A',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU4 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus04/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon15/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x5B',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU4 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus05/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon16/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x5C',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU5 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus05/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon16/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x5D',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU5 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus05/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon16/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x5E',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU5 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus06/Power_pout', {
								'object_path' : '/sys/class/hwmon/hwmon17/power2_input',
								'poll_interval' : 10000,
								'scale' : 1000000,
								'units' : 'W',
								'critical_upper' : 1760,
								'sensornumber' : '0x5F',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU6 Power Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus06/Voltage_vout', {
								'object_path' : '/sys/class/hwmon/hwmon17/in2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'V',
								'critical_upper' : 14.25,
								'critical_lower' : 10.5,
								'sensornumber' : '0x60',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU6 Voltage Output',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pmbus/pmbus06/temp_02', {
								'object_path' : '/sys/class/hwmon/hwmon17/temp2_input',
								'poll_interval' : 10000,
								'scale' : 1000,
								'units' : 'C',
								'critical_upper' : 95,
								'sensornumber' : '0x61',
								'sensor_type' : '0x09',
								'reading_type' : '0x01',
								'sensor_name' : 'PSU6 Temp 2',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pex/pex1_temp', {
								'object_path':'/tmp/pex/pex1_temp',
								'poll_interval' : 10000,
								'scale' : 1,
								'units' : 'C',
								'critical_upper' : 111,
								'sensornumber' : '0x37',
								'sensor_type' : '0x01',
								'reading_type' : '0x01',
								'sensor_name' : 'PEX1 Temp',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pex/pex2_temp', {
								'object_path':'/tmp/pex/pex2_temp',
								'poll_interval' : 10000,
								'scale' : 1,
								'units' : 'C',
								'critical_upper' : 111,
								'sensornumber' : '0x38',
								'sensor_type' : '0x01',
								'reading_type' : '0x01',
								'sensor_name' : 'PEX2 Temp',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pex/pex3_temp', {
								'object_path':'/tmp/pex/pex3_temp',
								'poll_interval' : 10000,
								'scale' : 1,
								'units' : 'C',
								'critical_upper' : 111,
								'sensornumber' : '0x39',
								'sensor_type' : '0x01',
								'reading_type' : '0x01',
								'sensor_name' : 'PEX3 Temp',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/pex/pex4_temp', {
								'object_path':'/tmp/pex/pex4_temp',
								'poll_interval' : 10000,
								'scale' : 1,
								'units' : 'C',
								'critical_upper' : 111,
								'sensornumber' : '0x3A',
								'sensor_type' : '0x01',
								'reading_type' : '0x01',
								'sensor_name' : 'PEX4 Temp',
								'reading_error_count' : 'N/A'
							}
	],
	['/org/openbmc/sensors/gpu/gpu1_mem_temp', { 
							'object_path' : '/tmp/gpu/gpu1_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x62',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU1 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu2_mem_temp', {
							'object_path' : '/tmp/gpu/gpu2_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x63',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU2 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu3_mem_temp', { 
							'object_path' : '/tmp/gpu/gpu3_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x64',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU3 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu4_mem_temp', { 
							'object_path' : '/tmp/gpu/gpu4_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x65',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU4 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu5_mem_temp', {
							'object_path' : '/tmp/gpu/gpu5_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x66',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU5 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu6_mem_temp', {
							'object_path' : '/tmp/gpu/gpu6_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x67',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU6 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu7_mem_temp', { 
							'object_path' : '/tmp/gpu/gpu7_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x68',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU7 Mem Temp',
							'reading_error_count' : 0
						}
	],
	['/org/openbmc/sensors/gpu/gpu8_mem_temp', { 
							'object_path' : '/tmp/gpu/gpu8_mem_temp',
							'poll_interval' : 5000,
							'scale' : 1,
							'units' : 'C',
							'critical_upper' : 85,
							'sensornumber' : '0x69',
							'sensor_type' : '0x01',
							'reading_type' : '0x01',
							'sensor_name' : 'GPU8 Mem Temp',
							'reading_error_count' : 0
						}
	],
]

HWMON_CONFIG = {
}

# Miscellaneous non-poll sensor with system specific properties.
# The sensor id is the same as those defined in ID_LOOKUP['SENSOR'].
MISC_SENSORS = {
}

# Set fan_algorithm config
#   FAN_DBUS_INTF_LOOKUP: {keys:[dbus bus name, dbus interface name]}
#   CHASSIS_POWER_STATE: set chassis power state object path
#   FAN_INPUT_OBJ: set fan input object path
#       - ["fan tach obj path", "pwm index mapping with fan tach"]
#   FAN_OUTPUT_OBJ: set fan out object path , eg: hwmon control fan speed or directly use pwm control pwm
#   OPEN_LOOP_PARAM: set openloop parameter
#       - paramA
#       - paramB
#       - paramC
#       - Low_Amb
#       - Up_Amb
#       - Low_Speed
#       - High_Speed
#   OPEN_LOOP_GROUPS_1: set openloop object path
#   CLOSE_LOOP_PARAM_1: set closeloop parameter
#       - g_Kp
#       - g_Ki
#       - g_Kd
#       - g_CPUVariable
#       - g_DIMMVariable
#       - sensor_tracking
#       - highest warning temp
#   CLOSE_LOOP_GROUPS_1: set closeloop  group001 object path, eg: CPU0/CPU1
#   CLOSE_LOOP_PARAM_2: set closeloop parameter
#       - g_Kp
#       - g_Ki
#       - g_Kd
#       - g_CPUVariable
#       - g_DIMMVariable
#       - sensor_tracking
#       - highest warning temp
#   CLOSE_LOOP_GROUPS_2: set closeloop  group002 object path, eg: DIMM
#   FAN_LED_OFF: set fan led command: off
#   FAN_LED_PORT0_ALL_BLUE: set fan led port0 command: all blue
#   FAN_LED_PORT1_ALL_BLUE: set fan led port1 command: all blue
#   FAN_LED_PORT0_ALL_RED: set fan led port0 command: all red
#   FAN_LED_PORT1_ALL_RED: set fan led port1 command: all red
#   PORT0_FAN_LED_RED_MASK: set fan led port0 register mask with red
#   PORT0_FAN_LED_BLUE_MASK: set fan led port0 register mask with blue
#   PORT1_FAN_LED_RED_MASK: set fan led port1 register mask with red
#   PORT1_FAN_LED_BLUE_MASK: set fan led port1 register mask with blue
#   FAN_LED_I2C_BUS: set fan led i2c bus
#   FAN_LED_I2C_SLAVE_ADDRESS: set fan led i2c slave address
FAN_ALGORITHM_CONFIG = {
    'FAN_DBUS_INTF_LOOKUP':
    {
        'CHASSIS_POWER_STATE': ['org.openbmc.control.Chassis', 'org.openbmc.control.Chassis'],
        'FAN_INPUT_OBJ' : ['org.openbmc.Sensors', 'org.openbmc.SensorValue'],
        'FAN_OUTPUT_OBJ' : ['org.openbmc', 'org.openbmc.Fan'],
        'OPEN_LOOP_GROUPS_1' : ['org.openbmc.Sensors', 'org.openbmc.SensorValue'],
        'CLOSE_LOOP_GROUPS_1' : ['org.openbmc.Sensors', 'org.openbmc.SensorValue'],
        'CLOSE_LOOP_GROUPS_2' : ['org.openbmc.Sensors', 'org.openbmc.SensorValue'],
	'CLOSE_LOOP_GROUPS_3' : ['org.openbmc.Sensors', 'org.openbmc.SensorValue'],
    },

    'CHASSIS_POWER_STATE': ['/org/openbmc/control/chassis0'],
    'FAN_INPUT_OBJ':
        [
            #"/org/openbmc/sensors/fan/fan_tacho1", "pwm1",
            #"/org/openbmc/sensors/fan/fan_tacho2", "pwm2",
            #"/org/openbmc/sensors/fan/fan_tacho3", "pwm3",
            #"/org/openbmc/sensors/fan/fan_tacho4", "pwm4",
            #"/org/openbmc/sensors/fan/fan_tacho5", "pwm5",
            #"/org/openbmc/sensors/fan/fan_tacho6", "pwm6",
            #"/org/openbmc/sensors/fan/fan_tacho7", "pwm1",
            #"/org/openbmc/sensors/fan/fan_tacho8", "pwm2",
            #"/org/openbmc/sensors/fan/fan_tacho9", "pwm3",
            #"/org/openbmc/sensors/fan/fan_tacho10", "pwm4",
            #"/org/openbmc/sensors/fan/fan_tacho11", "pwm5",
            #"/org/openbmc/sensors/fan/fan_tacho12", "pwm6",
            "/sys/devices/platform/ast_pwm_tacho.0/tacho%d_rpm",
            "SensorNumberList", #notfity following setting about SensorNumberList
            "0x11", #base sensor number
            "12", #releate sensor list size
        ],
    'FAN_OUTPUT_OBJ':
        [
            #"/org/openbmc/control/fan/fan1",
            #"/org/openbmc/control/fan/fan2",
            #"/org/openbmc/control/fan/fan3",
            #"/org/openbmc/control/fan/fan4",
            #"/org/openbmc/control/fan/fan5",
            #"/org/openbmc/control/fan/fan6",
            "/org/openbmc/control/fan/pwm",
            "SensorNumberList", #notfity following setting about SensorNumberList
            "0x1D", #base sensor number
            "6", #releate sensor list size
        ],
    'OPEN_LOOP_PARAM':
        [
            #'0',
            #'2',
            #'0',
            #'20',
            #'38',
            #'50',
            #'100',
            '0',
            '1',
            '0',
            '30',
            '38',
            '30',
            '100',
        ],
    'OPEN_LOOP_GROUPS_1':
        [
            #"/org/openbmc/sensors/temperature/TMP1",
            #"/org/openbmc/sensors/temperature/TMP2",
            #"/org/openbmc/sensors/temperature/TMP3",
            #"/org/openbmc/sensors/temperature/TMP4",
            #"/org/openbmc/sensors/temperature/TMP5",
            #"/org/openbmc/sensors/temperature/TMP6",
            #"/org/openbmc/sensors/temperature/TMP7",
            #"/org/openbmc/sensors/temperature/TMP8",
            "/sys/class/hwmon/hwmon1/temp1_input",
            "/sys/class/hwmon/hwmon2/temp1_input",
        ],
    'CLOSE_LOOP_PARAM_1' :
        [
            #'0.45',
            #'-0.017',
            #'0.3',
            #'70',
            #'85',
            '0.35',
            '-0.015',
            '0.4',
            '70',
            '81',
        ],
    'CLOSE_LOOP_GROUPS_1':
        [
            #"/org/openbmc/sensors/gpu/gpu1_temp",
            #"/org/openbmc/sensors/gpu/gpu2_temp",
            #"/org/openbmc/sensors/gpu/gpu3_temp",
            #"/org/openbmc/sensors/gpu/gpu4_temp",
            #"/org/openbmc/sensors/gpu/gpu5_temp",
            #"/org/openbmc/sensors/gpu/gpu6_temp",
            #"/org/openbmc/sensors/gpu/gpu7_temp",
            #"/org/openbmc/sensors/gpu/gpu8_temp",
            "/tmp/gpu/gpu%d_temp",
            "SensorNumberList", #notfity following setting about SensorNumberList
            "0x41", #base sensor number
            "8", #releate sensor list size
        ],
    'CLOSE_LOOP_PARAM_2' :
        [
            '0.35',
            '-0.015',
            '0.4',
            '90',
            '111',
        ],
    'CLOSE_LOOP_GROUPS_2':
        [
            #"/org/openbmc/sensors/pex/pex0",
            #"/org/openbmc/sensors/pex/pex1",
            #"/org/openbmc/sensors/pex/pex2",
            #"/org/openbmc/sensors/pex/pex3",
            "/tmp/pex/pex%d_temp",
            "SensorNumberList", #notfity following setting about SensorNumberList
            "0x37", #base sensor number
            "4", #releate sensor list size
        ],
    'CLOSE_LOOP_PARAM_3' :
        [
            '0.7',
            '-0.03',
            '0.4',
            '75',
            '85',
        ],
    'CLOSE_LOOP_GROUPS_3':
        [
            "/tmp/gpu/gpu%d_mem_temp",
            "SensorNumberList", #notfity following setting about SensorNumberList
            "0x62", #base sensor number
            "8", #releate sensor list size
        ],

    'FAN_LED_OFF': ["0xFF"],
    'FAN_LED_PORT0_ALL_BLUE': ["0xAA"],
    'FAN_LED_PORT1_ALL_BLUE': ["0x55"],
    'FAN_LED_PORT0_ALL_RED': ["0x55"],
    'FAN_LED_PORT1_ALL_RED': ["0xAA"],
    'PORT0_FAN_LED_RED_MASK': ["0x02"],
    'PORT0_FAN_LED_BLUE_MASK': ["0x01"],
    'PORT1_FAN_LED_RED_MASK': ["0x40"],
    'PORT1_FAN_LED_BLUE_MASK': ["0x80"],
    'FAN_LED_SPEED_LIMIT': ["30"],

    'FAN_LED_I2C_BUS': [],
    'FAN_LED_I2C_SLAVE_ADDRESS': [],
}
