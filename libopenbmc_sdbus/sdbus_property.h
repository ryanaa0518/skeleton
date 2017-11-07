
#ifndef __H_SDBUS_PROPERTY__
#define __H_SDBUS_PROPERTY__

#include <systemd/sd-bus.h>

int set_dbus_property(sd_bus *bus, char *objpath, char *property_name, char *property_type, void *property_value, int property_identify);

#endif
