#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <dirent.h>
#include <systemd/sd-bus.h>

static int
__set_dbus_property(sd_bus *bus, char *objpath, char *property_name, char *property_type, void *property_value)
{
	sd_bus_error bus_error = SD_BUS_ERROR_NULL;
	sd_bus_message *response = NULL;
	int rc = 0;

	if (property_value == NULL || property_type == NULL || property_name==NULL || objpath == NULL)
		return 0;

	if (bus == NULL)
		return -1;

	if (property_type[0] == 'i') {
		rc = sd_bus_call_method(bus,
					"org.openbmc.Sensors",
					objpath,
					"org.freedesktop.DBus.Properties",
					"Set",
					&bus_error,
					&response,
					"ssv",
					"org.openbmc.HwmonSensor", property_name, "i",
					*((int *) property_value)
				       );
		sd_bus_error_free(&bus_error);
		sd_bus_message_unref(response);
	} else if (property_type[0] == 's') {
		rc = sd_bus_call_method(bus,
					"org.openbmc.Sensors",
					objpath,
					"org.freedesktop.DBus.Properties",
					"Set",
					&bus_error,
					&response,
					"ssv",
					"org.openbmc.HwmonSensor", property_name, "s",
					(char *)property_value
				       );
		sd_bus_error_free(&bus_error);
		sd_bus_message_unref(response);
	} else
		rc = -1;

	if(rc < 0) {
		printf("%s, %d response message:[%s]\n", __FUNCTION__, __LINE__, strerror(-rc));
	}
	return rc;
}

//param: property_identify: it maybe be "sensor number" or "index" for identifing property_name
int
set_dbus_property(sd_bus *bus, char *objpath, char *property_name, char *property_type, void *property_value, int property_identify)
{
	char temp_property_name[100] = {0};
	if (property_identify == -1)
		strcpy(temp_property_name, property_name);
	else
		sprintf(temp_property_name, "%s_%d", property_name, property_identify);
	return __set_dbus_property(bus, objpath, temp_property_name, property_type, property_value);
}

