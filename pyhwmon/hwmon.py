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
from obmc.events import Event
from obmc.events import EventManager
from obmc.sensors import SensorValue as SensorValue
from obmc.sensors import HwmonSensor as HwmonSensor
from obmc.sensors import SensorThresholds as SensorThresholds
import obmc_system_config as System

SENSOR_BUS = 'org.openbmc.Sensors'
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
		self.scanDirectory()
		self.event_manager = EventManager()
		gobject.timeout_add(DIR_POLL_INTERVAL, self.scanDirectory)

	def readAttribute(self,filename):
		val = "N/A"
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

	def poll(self,objpath,attribute):
		try:
			if attribute != '':
				try:
					raw_value = int(self.readAttribute(attribute))
				except:
					raw_value = "N/A"
			else:
				raw_value = "N/A"
			if raw_value == "N/A":
				return False
			obj = bus.get_object(SENSOR_BUS,objpath,introspect=False)
			intf = dbus.Interface(obj,HwmonSensor.IFACE_NAME)
			rtn = intf.setByPoll(raw_value)
			if (rtn[0] == True):
				self.writeAttribute(attribute,rtn[1])
			intf_p = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
			threshold_state = intf_p.Get(SensorThresholds.IFACE_NAME, 'threshold_state')
			if threshold_state != self.threshold_state[objpath]:
				origin_threshold_type = self.threshold_state[objpath]
				self.threshold_state[objpath]  = threshold_state
				if threshold_state == 'NORMAL':
					event_dir = 'Deasserted'
				else:
					event_dir = 'Asserted'

				self.threshold_state[objpath]  = threshold_state
				scale = intf_p.Get(HwmonSensor.IFACE_NAME, 'scale')
				real_reading = raw_value / scale
				self.LogThresholdEventMessages(objpath, threshold_state, origin_threshold_type, event_dir, real_reading)
		except:
			print "HWMON: Attibute no longer exists: "+attribute
			self.sensors.pop(objpath,None)
			return False
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
			desc = sensor_name+' '+threshold_type_str+' going high-'+event_dir+": Reading "+str(reading)+", Threshold: "+str(threshold)
		elif threshold_type == 'LOWER_CRITICAL':
			threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_lower')
			desc = sensor_name+' '+threshold_type_str+' going low-'+event_dir+": Reading "+str(reading)+", Threshold: "+str(threshold)
		else:
			threshold = 'N/A'
			if origin_threshold_type == 'UPPER_CRITICAL':
				threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_upper')
			if origin_threshold_type == 'LOWER_CRITICAL':
				threshold = intf.Get(SensorThresholds.IFACE_NAME, 'critical_lower')
			desc = sensor_name+' '+threshold_type_str+' '+event_dir+" from "+str(origin_threshold_type)+": Reading "+str(reading)+", Threshold: "+str(threshold)

		# Add event log
		severity = Event.SEVERITY_ERR if event_dir == 'Asserted' else Event.SEVERITY_INFO
		log = Event(severity, desc, sensortype, sensor_number)
		self.event_manager.add_log(log)

		return True

	def addObject(self,dpath,hwmon_path,hwmon):
		objsuf = hwmon['object_path']
		objpath = SENSOR_PATH+'/'+objsuf
		
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
			# init value as N/A
			intf.Set(SensorValue.IFACE_NAME,'value','N/A')
			
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

			gobject.timeout_add(hwmon['poll_interval'],self.poll,objpath,hwmon_path)

	def addSensorMonitorObject(self):
		if "SENSOR_MONITOR_CONFIG" not in dir(System):
			return

		for i in range(len(System.SENSOR_MONITOR_CONFIG)):
			objpath = System.SENSOR_MONITOR_CONFIG[i][0]
			hwmon = System.SENSOR_MONITOR_CONFIG[i][1]

			if 'object_path' not in hwmon:
				print "Warnning[addSensorMonitorObject]: Not correct set [object_path]"
				continue

			hwmon_path = hwmon['object_path']
			if (self.sensors.has_key(objpath) == False):
				## register object with sensor manager
				obj = bus.get_object(SENSOR_BUS,SENSOR_PATH,introspect=False)
				intf = dbus.Interface(obj,SENSOR_BUS)
				intf.register("HwmonSensor",objpath)

				## set some properties in dbus object
				obj = bus.get_object(SENSOR_BUS,objpath,introspect=False)
				intf = dbus.Interface(obj,dbus.PROPERTIES_IFACE)
				intf.Set(HwmonSensor.IFACE_NAME,'filename',hwmon_path)
				# init value as N/A
				val = 'N/A'
				if hwmon.has_key('value'):
					val = hwmon['value']
				intf.Set(SensorValue.IFACE_NAME,'value', val)

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
					gobject.timeout_add(hwmon['poll_interval'],self.poll,objpath,hwmon_path)
	
	def scanDirectory(self):
	 	devices = os.listdir(HWMON_PATH)
		found_hwmon = {}
		regx = re.compile('([a-z]+)\d+\_')
		for d in devices:
			dpath = HWMON_PATH+'/'+d+'/'
			found_hwmon[dpath] = True
			if (self.hwmon_root.has_key(dpath) == False):
				self.hwmon_root[dpath] = []
			## the instance name is a soft link
			instance_name = os.path.realpath(dpath+'device').split('/').pop()
			
			
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

