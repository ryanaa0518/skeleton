#!/usr/bin/python -u

import os
import sys
import gobject
import subprocess
import dbus
import dbus.service
import dbus.mainloop.glib
import obmc.dbuslib.propertycacher as PropertyCacher
from obmc.dbuslib.bindings import get_dbus, DbusProperties, DbusObjectManager
from obmc.sensors import HwmonSensor as HwmonSensor
from obmc.sensors import SensorThresholds as SensorThresholds
from obmc.events import EventManager, Event
import obmc_system_config as System

import mac_guid

DBUS_NAME = 'org.openbmc.Sensors'
DBUS_INTERFACE = 'org.freedesktop.DBus.Properties'
SENSOR_VALUE_INTERFACE = 'org.openbmc.SensorValue'

g_bmchealth_obj_path = "/org/openbmc/sensors/bmc_health"

_EVENT_MANAGER = EventManager()

def LogEventBmcHealthMessages(event_dir, evd1, evd2, evd3):
    bus = get_dbus()
    objpath = g_bmchealth_obj_path
    obj = bus.get_object(DBUS_NAME, objpath, introspect=False)
    intf = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
    sensortype = intf.Get(HwmonSensor.IFACE_NAME, 'sensor_type')
    sensor_number = intf.Get(HwmonSensor.IFACE_NAME, 'sensornumber')
    sensor_name = objpath.split('/').pop()

    if event_dir == 'Asserted':
        sev = "Critical"
    else:
        sev = "Information"

    desc = sensor_name + ":"
    details = ""
    logid = 0
    if 'LOG_EVENT_CONFIG' in dir(System):
        for log_item in System.LOG_EVENT_CONFIG:
            if log_item['EVD1'].lower() == evd1.lower() and log_item['EVD2'].lower() == evd2.lower() \
              and log_item['EVD3'].lower() == evd3.lower():
                desc+="EVD1:" + log_item['EVD1'] + ","
                desc+="EVD2:" + log_item['EVD2'] + ","
                desc+="EVD3:" + log_item['EVD3'] + ":"
                desc+=log_item['health_indicator']
                if log_item['description'] != '':
                    desc+="-" + log_item['description']
                details = log_item['detail']
                debug = dbus.ByteArray("")

                #prepare to send log event:
                #create & init new event class
                log = Event(sev, desc, str(sensortype), str(sensor_number), details, debug)
                #add new event log
                logid=_EVENT_MANAGER.add_log(log)
                break

    if logid == 0:
        return False
    else:
        return True

def bmchealth_set_value(val):
    try:
        b_bus = get_dbus()
        b_obj= b_bus.get_object(DBUS_NAME, g_bmchealth_obj_path)
        b_interface = dbus.Interface(b_obj,  DBUS_INTERFACE)
        b_interface.Set(SENSOR_VALUE_INTERFACE, 'value', val)
    except:
        print "bmchealth_set_value Error!!!"
        return -1
    return 0

def bmchealth_check_network():
    carrier_file_path = "/sys/class/net/eth0/carrier"
    operstate_file_path = "/sys/class/net/eth0/operstate"
    check_ipaddr_command ="ifconfig eth0"
    check_ipaddr_keywords = "inet addr"
    record_dhcp_file_path = "/tmp/bmchealth_record_dhcp_status.txt"
    record_down_file_path = "/tmp/bmchealth_record_down_status.txt"

    carrier = ""    #0 or 1
    operstate = ""  #up or down
    ipaddr = ""

    g_dhcp_status = 1
    g_net_down_status = 1

    try:
        with open(record_dhcp_file_path, 'r') as f:
            for line in f:
                g_dhcp_status = int(line.rstrip('\n'))
    except:
        pass
    try:
        with open(record_down_file_path, 'r') as f:
            for line in f:
                g_net_down_status = int(line.rstrip('\n'))
    except:
        pass

    org_dhcp_status = g_dhcp_status
    org_down_status = g_net_down_status
    try:
        cmd_data = subprocess.check_output(check_ipaddr_command, shell=True)
        if cmd_data.find(check_ipaddr_keywords) >=0:
            ipaddr = "1"
        else:
            ipaddr = "0"
    except:
        print "[bmchealth_check_network]Error conduct operstate!!!"
        return False

    try:
        with open(carrier_file_path, 'r') as f:
            for line in f:
                carrier = line.rstrip('\n')
    except:
        print "[bmchealth_check_network]Error conduct carrier!!!"
        return False

    try:
        with open(operstate_file_path, 'r') as f:
            for line in f:
                operstate = line.rstrip('\n')
    except:
        print "[bmchealth_check_network]Error conduct operstate!!!"
        return False

    #check dhcp fail status
    if ipaddr == "0" and carrier == "1" and operstate == "up":
        if g_dhcp_status == 1:
            print "bmchealth_check_network:  DHCP Fail"
            g_dhcp_status = 0
            bmchealth_set_value(0x1)
            LogEventBmcHealthMessages("Asserted", "0x1", "0x2", "" )
    else:
        g_dhcp_status = 1

    #check network down
    if carrier == "0" and operstate=="down":
        if g_net_down_status == 1:
            print "bmchealth_check_network:  network down Fail"
            g_net_down_status = 0
            bmchealth_set_value(0x1)
            LogEventBmcHealthMessages("Asserted", "0x1", "0x1", "" )
    else:
        g_net_down_status = 1

    if org_dhcp_status != g_dhcp_status:
        with open(record_dhcp_file_path, 'w') as f:
            f.write(str(g_dhcp_status))
    if org_down_status != g_net_down_status:
        with open(record_down_file_path, 'w') as f:
            f.write(str(g_net_down_status))
    return True

def bmchealth_fix_and_check_mac():
    print "fix-mac & fix-guid start"
    fix_mac_status = mac_guid.fixMAC()
    fix_guid_status = mac_guid.fixGUID()

    print "bmchealth: check mac status:" + str(fix_mac_status)
    print "bmchealth: check guid status:" + str(fix_guid_status)
    #check bmchealth macaddress
    ret = 0
    if fix_mac_status == 0 or fix_guid_status == 0:
        ret = bmchealth_set_value(0xC)
        LogEventBmcHealthMessages("Asserted", "0xC", "", "" )
    print "bmchealth: bmchealth_fix_and_check_mac : " + str(ret)
    return ret

if __name__ == '__main__':
    mainloop = gobject.MainLoop()
    #set bmchealth default value
    bmchealth_set_value(0)
    bmchealth_fix_and_check_mac()
    gobject.timeout_add(1000,bmchealth_check_network)
    print "bmchealth_handler control starting"
    mainloop.run()
