#!/usr/bin/python -u

import sys
import os
import gobject
import glob
import dbus
import dbus.service
import dbus.mainloop.glib
import re
from obmc.dbuslib.bindings import get_dbus

from obmc.sensors import SensorValue as SensorValue
from obmc.sensors import HwmonSensor as HwmonSensor
from obmc.sensors import SensorThresholds as SensorThresholds
import obmc_system_config as System

SENSOR_BUS = 'org.openbmc.Sensors'
# sensors include /org/openbmc/sensors and /org/openbmc/control
SENSORS_OBJPATH = '/org/openbmc'
SENSOR_PATH = '/org/openbmc/sensors'
DIR_POLL_INTERVAL = 30000
HWMON_PATH = '/sys/class/hwmon'

## static define which interface each property is under
## need a better way that is not slow
IFACE_LOOKUP = {
	'units' : SensorValue.IFACE_NAME,
	'scale' : HwmonSensor.IFACE_NAME,
	'offset' : HwmonSensor.IFACE_NAME,
	'critical_upper' : SensorThresholds.IFACE_NAME,
	'warning_upper' : SensorThresholds.IFACE_NAME,
	'critical_lower' : SensorThresholds.IFACE_NAME,
	'warning_lower' : SensorThresholds.IFACE_NAME,
	'emergency_enabled' : SensorThresholds.IFACE_NAME,
	'sensornumber': HwmonSensor.IFACE_NAME,
	'sensor_name': HwmonSensor.IFACE_NAME,
	'sensor_type': HwmonSensor.IFACE_NAME,
	'reading_type': HwmonSensor.IFACE_NAME,
	'min_reading': HwmonSensor.IFACE_NAME,
	'max_reading': HwmonSensor.IFACE_NAME,
}

class Hwmons():
	def __init__(self,bus):
		self.sensors = { }
		self.hwmon_root = { }
		self.threshold_state = {}
		self.pgood_obj = bus.get_object('org.openbmc.control.Power', '/org/openbmc/control/power0', introspect=False)
		self.pgood_intf = dbus.Interface(self.pgood_obj,dbus.PROPERTIES_IFACE)
		self.path_mapping = {}
		self.scanDirectory()
		gobject.timeout_add(DIR_POLL_INTERVAL, self.scanDirectory)   

	def readAttribute(self,filename):
		val = "-1"
		try:
			with open(filename, 'r') as f:
				for line in f:
					val = line.rstrip('\n')
		except (OSError, IOError):
			print "Cannot read attributes:", filename
		return val

	def writeAttribute(self,filename,value):
		with open(filename, 'w') as f:
			f.write(str(value)+'\n')

	def check_thresholds(self, threshold_props, value, hwmon):
		sn = hwmon['sensornumber']
		thresholds = ['critical_upper', 'critical_lower', \
						'warning_upper', 'warning_lower']
		if hwmon['thresholds_enabled'] is False:
			return "NORMAL"
		for threshold in thresholds:
			try:
				hwmon[threshold] = threshold_props[threshold+'_'+str(sn)]
			except KeyError:
				pass
		current_state = hwmon['threshold_state']
		if current_state.find("NORMAL") != -1:
			if (hwmon['critical_upper'] != None) and \
					(value >= hwmon['critical_upper']):
				current_state = "UPPER_CRITICAL"
			elif (hwmon['critical_lower'] != None) and \
					(value <= hwmon['critical_lower']):
				current_state = "LOWER_CRITICAL"
			elif (hwmon['warning_upper'] != None) and \
					(value >= hwmon['warning_upper']):
				current_state = "UPPER_WARNING"
			elif (hwmon['warning_lower'] != None) and \
					(value <= hwmon['warning_lower']):
				current_state = "LOWER_WARNING"
		elif current_state.find("UPPER_CRITICAL") >= 0:
			if (hwmon['critical_upper'] != None) and \
					(value <= hwmon['critical_upper'] -
							(hwmon['positive_hysteresis'] + 1)):
				current_state = "NORMAL"
		elif current_state.find("LOWER_CRITICAL") >= 0:
			if (hwmon['critical_lower'] != None) and \
					(value >= hwmon['critical_lower'] +
							(hwmon['negative_hysteresis'] + 1)):
				current_state = "NORMAL"
		elif current_state.find("UPPER_WARNING") >= 0:
			if (hwmon['warning_upper'] != None) and \
					(value <= hwmon['warning_upper'] -
							(hwmon['positive_hysteresis'] + 1)):
				current_state = "NORMAL"
		elif current_state.find("LOWER_WARNING") >= 0:
			if (hwmon['warning_lower'] != None) and \
					(value >= hwmon['warning_lower'] +
							(hwmon['negative_hysteresis'] + 1)):
				current_state = "NORMAL"

		hwmon['threshold_state'] = current_state
		worst = hwmon['worst_threshold_state']
		if (current_state.find("CRITICAL") != -1 or
				(current_state.find("WARNING") != -1 and worst.find("CRITICAL") == -1)):
			hwmon['worst_threshold_state'] = current_state

		return current_state


	def poll(self,objpath,attribute,hwmon):
		try:
			standby_monitor = True
			if hwmon.has_key('standby_monitor'):
				standby_monitor = hwmon['standby_monitor']
			# Skip monitor while DC power off if stand by monitor is False

			obj = bus.get_object(SENSOR_BUS,objpath,introspect=False)
			intf_p = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
			intf = dbus.Interface(obj,HwmonSensor.IFACE_NAME)
			raw_value = int(self.readAttribute(attribute))
			rtn = intf.setByPoll(raw_value)
			if (rtn[0] == True):
				self.writeAttribute(attribute,rtn[1])
			if not standby_monitor:
				current_pgood = self.pgood_intf.Get('org.openbmc.control.Power', 'pgood')
				if  current_pgood == 0:
					intf_p.Set(SensorValue.IFACE_NAME,'value','N/A')
					return True

			# do not check threshold while not reading
			if raw_value == -1:
				return True
			threshold_state = intf_p.Get(SensorThresholds.IFACE_NAME, 'threshold_state')
			if threshold_state != self.threshold_state[objpath]:
				origin_threshold_type = self.threshold_state[objpath]
				self.threshold_state[objpath]  = threshold_state
				if threshold_state == 'NORMAL':
					origin_threshold_type  = self.threshold_state[objpath]
					event_dir = 'Deasserted'
				else:
					origin_threshold_type  = threshold_state
					event_dir = 'Asserted'
				self.threshold_state[objpath]  = threshold_state
				scale = intf_p.Get(HwmonSensor.IFACE_NAME, 'scale')
				real_reading = raw_value / scale
				self.LogThresholdEventMessages(objpath, threshold_state, origin_threshold_type, event_dir, real_reading)
		except:
			print "HWMON: Attibute no longer exists: "+attribute
			raw_value = "N/A"
			self.sensors.pop(objpath,None)
			return True


		return True


	def LogThresholdEventMessages(self, objpath, threshold_type, origin_threshold_type, event_dir, reading):
	
		obj = bus.get_object(SENSOR_BUS, objpath, introspect=False)
		intf = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
		sensortype = intf.Get(HwmonSensor.IFACE_NAME, 'sensor_type')
		sensor_number = intf.Get(HwmonSensor.IFACE_NAME, 'sensornumber')
		sensor_name = objpath.split('/').pop()
		threshold_type_str = threshold_type.title().replace('_', ' ')

		#Get event messages
		if threshold_type == 'UPPER_CRITICAL':
			threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_upper')
			desc = sensor_name+' '+threshold_type_str+' going high-'+event_dir+": Reading "+str(reading)+", Threshold "+str(threshold)
		elif threshold_type == 'LOWER_CRITICAL':
			threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_lower')
			desc = sensor_name+' '+threshold_type_str+' going low-'+event_dir+": Reading "+str(reading)+", Threshold "+str(threshold)
		else:
			threshold = 'N/A'
			if origin_threshold_type == 'UPPER_CRITICAL':
				threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_upper')
			if origin_threshold_type == 'LOWER_CRITICAL':
				threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_lower')
			print str(threshold) + ' back to normal\n'
			desc = sensor_name+' '+threshold_type_str+' '+event_dir+" from "+str(origin_threshold_type)+": Reading "+str(reading)+", Threshold "+str(threshold)

		#Get Severity
		if event_dir == 'Asserted':
			sev = "Critical"
		else:
			sev = "Information"

		details = ""
		debug = dbus.ByteArray("")

		event_obj = bus.get_object("org.openbmc.records.events",
									"/org/openbmc/records/events",
									introspect=False)
		event_intf = dbus.Interface(event_obj, "org.openbmc.recordlog")
		event_intf.acceptBMCMessage(sev, desc, str(sensortype), str(sensor_number), details, debug)

		return True
	
	def addObject(self,dpath,hwmon_path,hwmon):
		objsuf = hwmon['object_path']
		objpath = SENSORS_OBJPATH+'/'+objsuf
		
		if (self.sensors.has_key(objpath) == False):
			print "HWMON add: "+objpath+" : "+hwmon_path

			## register object with sensor manager
			obj = bus.get_object(SENSOR_BUS,SENSOR_PATH,introspect=False)
			intf = dbus.Interface(obj,SENSOR_BUS)
			intf.register("HwmonSensor",objpath)

			## set some properties in dbus object		
			obj = bus.get_object(SENSOR_BUS,objpath,introspect=False)
			intf = dbus.Interface(obj,dbus.PROPERTIES_IFACE)
			intf.Set(HwmonSensor.IFACE_NAME,'filename',hwmon_path)
			
			## check if one of thresholds is defined to know
			## whether to enable thresholds or not
			if (hwmon.has_key('critical_upper') or hwmon.has_key('critical_lower')):
				intf.Set(SensorThresholds.IFACE_NAME,'thresholds_enabled',True)

			for prop in hwmon.keys():
				if (IFACE_LOOKUP.has_key(prop)):
					intf.Set(IFACE_LOOKUP[prop],prop,hwmon[prop])
					print "Setting: "+prop+" = "+str(hwmon[prop])

			self.sensors[objpath]=True
			self.hwmon_root[dpath].append(objpath)
			self.threshold_state[objpath] = "NORMAL"

			gobject.timeout_add(hwmon['poll_interval'],self.poll,objpath,hwmon_path,hwmon)

	def addSensorMonitorObject(self):
		if "SENSOR_MONITOR_CONFIG" not in dir(System):
			return

		for i in range(len(System.SENSOR_MONITOR_CONFIG)):
			objpath = System.SENSOR_MONITOR_CONFIG[i][0]
			hwmon = System.SENSOR_MONITOR_CONFIG[i][1]

			if 'device_node' not in hwmon:
				print "Warnning[addSensorMonitorObject]: Not correct set [device_node]"
				continue

			if 'bus_number' in hwmon:
				if hwmon['bus_number'] in self.path_mapping:
					hwmon_path = self.path_mapping[hwmon['bus_number']] + hwmon['device_node']
				else:
					hwmon_path = 'N/A'
			else:
				hwmon_path = hwmon['device_node']
			if (self.sensors.has_key(objpath) == False):
				## register object with sensor manager
				obj = bus.get_object(SENSOR_BUS,SENSOR_PATH,introspect=False)
				intf = dbus.Interface(obj,SENSOR_BUS)
				intf.register("HwmonSensor",objpath)

				## set some properties in dbus object
				obj = bus.get_object(SENSOR_BUS,objpath,introspect=False)
				intf = dbus.Interface(obj,dbus.PROPERTIES_IFACE)
				intf.Set(HwmonSensor.IFACE_NAME,'filename',hwmon_path)

				# init value as
				val = -1
				if hwmon.has_key('value'):
					val = hwmon['value']
					intf_h = dbus.Interface(obj,HwmonSensor.IFACE_NAME)
					intf_h.setByPoll(val)

				## check if one of thresholds is defined to know
				## whether to enable thresholds or not
				if (hwmon.has_key('critical_upper') or hwmon.has_key('critical_lower')):
					intf.Set(SensorThresholds.IFACE_NAME,'thresholds_enabled',True)

				for prop in hwmon.keys():
					if (IFACE_LOOKUP.has_key(prop)):
						intf.Set(IFACE_LOOKUP[prop],prop,hwmon[prop])

				self.sensors[objpath]=True
				self.threshold_state[objpath] = "NORMAL"
				if hwmon.has_key('poll_interval'):
					gobject.timeout_add(hwmon['poll_interval'],self.poll,objpath,hwmon_path,hwmon)
	
	def scanDirectory(self):
	 	devices = os.listdir(HWMON_PATH)
		found_hwmon = {}
		regx = re.compile('([a-z]+)\d+\_')
		self.path_mapping = {}
		for d in devices:
			dpath = HWMON_PATH+'/'+d+'/'
			found_hwmon[dpath] = True
			if (self.hwmon_root.has_key(dpath) == False):
				self.hwmon_root[dpath] = []
			## the instance name is a soft link
			instance_name = os.path.realpath(dpath+'device').split('/').pop()
			self.path_mapping[instance_name] = dpath
			
			if (System.HWMON_CONFIG.has_key(instance_name)):
				hwmon = System.HWMON_CONFIG[instance_name]
	 			
				if (hwmon.has_key('labels')):
					label_files = glob.glob(dpath+'/*_label')
					for f in label_files:
						label_key = self.readAttribute(f)
						if (hwmon['labels'].has_key(label_key)):
							namef = f.replace('_label','_input')
							self.addObject(dpath,namef,hwmon['labels'][label_key])
						else:
							pass
							#print "WARNING - hwmon: label ("+label_key+") not found in lookup: "+f
							
				if hwmon.has_key('names'):
					for attribute in hwmon['names'].keys():
						self.addObject(dpath,dpath+attribute,hwmon['names'][attribute])
						
			else:
				print "WARNING - hwmon: Unhandled hwmon: "+dpath
	
		self.addSensorMonitorObject()
		for k in self.hwmon_root.keys():
			if (found_hwmon.has_key(k) == False):
				## need to remove all objects associated with this path
				print "Removing: "+k
				for objpath in self.hwmon_root[k]:
					if (self.sensors.has_key(objpath) == True):
						print "HWMON remove: "+objpath
						self.sensors.pop(objpath,None)
						obj = bus.get_object(SENSOR_BUS,SENSOR_PATH,introspect=False)
						intf = dbus.Interface(obj,SENSOR_BUS)
						intf.delete(objpath)

				self.hwmon_root.pop(k,None)
				
		return True

			
if __name__ == '__main__':
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	bus = get_dbus()
	root_sensor = Hwmons(bus)
	mainloop = gobject.MainLoop()

	print "Starting HWMON sensors"
	mainloop.run()

