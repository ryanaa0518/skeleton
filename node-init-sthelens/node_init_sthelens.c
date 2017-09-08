#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

/*----------------------------------------------------------------*/
/* Main Event Loop                                                */
#define PHYSICAL_I2C 7
#define PSU_NUM 6

int
main(int argc, char *argv[])
{
    char buff_path[256] = "";
    int i = 0;

    /* Init pmbus node */
    for(i=1; i<=PSU_NUM; i++)
    {
        sprintf(buff_path, "echo pmbus 0x58 > /sys/bus/i2c/devices/i2c-%d/new_device", PHYSICAL_I2C+i);
        printf("%s\n", buff_path);
        system(buff_path);
    }

    /* fix-mac & fix-guid */
    printf("fix-mac & fix-guid start");
    system("/usr/sbin/mac_guid.py --fix-mac");
    system("/usr/sbin/mac_guid.py --fix-guid");

    return 0;
}
