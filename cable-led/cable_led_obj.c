#include <stdio.h>
#include <openbmc_intf.h>
#include <gpio.h>
#include <openbmc.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <systemd/sd-bus.h>

typedef struct {
	int gpioNumA32Present;
	int gpioNumB9Present;
	int gpioNumPresent;
	int gpioNumLED;
} CableLedStruct;

#define CABLE_SW1 0
#define CABLE_SW2 1
#define CABLE_SW3 2
#define CABLE_SW4 3
#define PORT1A    0
#define PORT1B    1
#define PORT2A    2
#define PORT2B    3
#define MAX_CABLE_SW 4
#define MAX_CABLE_PORT 4

CableLedStruct CableLed[4][4];

/* ------------------------------------------------------------------------- */
int read_cable_status(int cable_sw, int cable_port)
{
	int rc = -1;
	char cable_prsent_path1[128] = {0};
	char cable_prsent_path2[128] = {0};
	int len = 0;
	int A32Present = 0;
	int B9Present = 0;

	//Read A32 Present pin
	len = snprintf(cable_prsent_path1, sizeof(cable_prsent_path1),
		       "/sys/class/gpio/gpio%d/value", CableLed[cable_sw][cable_port].gpioNumA32Present);

	FILE *fp1 = fopen(cable_prsent_path1,"r");
	if(fp1 == NULL) {
		return 0;
	}

	fscanf(fp1, "%d", &A32Present);

	fclose(fp1);

	//Read B9 Present pin
	len = snprintf(cable_prsent_path2, sizeof(cable_prsent_path2),
		       "/sys/class/gpio/gpio%d/value", CableLed[cable_sw][cable_port].gpioNumB9Present);

	FILE *fp2 = fopen(cable_prsent_path2,"r");
	if(fp2 == NULL) {
		return 0;
	}

	fscanf(fp2, "%d", &B9Present);

	fclose(fp2);

	return (A32Present | B9Present);
}

void set_cable_led(int cable_sw, int cable_port, const char *control)
{
	char cable_led_path[128] = {0};
	int len = 0;

	len = snprintf(cable_led_path, sizeof(cable_led_path),
		       "/sys/class/gpio/gpio%d/value", CableLed[cable_sw][cable_port].gpioNumLED);

	FILE *fp = fopen(cable_led_path,"w");
	if(fp == NULL) {
		return;
	}

	fwrite(control, strlen(control), 1, fp);

	fclose(fp);

	return;
}

void set_present(int cable_sw, int cable_port, const char *control)
{
	char cable_led_path[128] = {0};
	int len = 0;

	len = snprintf(cable_led_path, sizeof(cable_led_path),
		       "/sys/class/gpio/gpio%d/value", CableLed[cable_sw][cable_port].gpioNumPresent);

	FILE *fp = fopen(cable_led_path,"w");
	if(fp == NULL) {
		return;
	}

	fwrite(control, strlen(control), 1, fp);

	fclose(fp);

	return;
}

void check_cable_status()
{
	int i = 0, j = 0;
	int cable_failed = 0;

	while(1) {
		for(i=0; i<MAX_CABLE_SW; i++) {
			for(j=0; j<MAX_CABLE_PORT; j++) {
				cable_failed = read_cable_status(i, j);
				if(cable_failed) {
					set_cable_led(i, j, "1"); //set on cable led
					set_present(i, j, "1");
				} else {
					set_cable_led(i, j, "0"); //set off cable led
					set_present(i, j, "0");
				}
			}
		}
		sleep(1);
	}
}

void init_cable_gpio_mapping()
{
	CableLed[CABLE_SW1][PORT1A].gpioNumA32Present = 228;
	CableLed[CABLE_SW1][PORT1A].gpioNumB9Present = 229;
	CableLed[CABLE_SW1][PORT1B].gpioNumA32Present = 230;
	CableLed[CABLE_SW1][PORT1B].gpioNumB9Present = 231;
	CableLed[CABLE_SW1][PORT1A].gpioNumPresent = 232;
	CableLed[CABLE_SW1][PORT1B].gpioNumPresent = 233;
	CableLed[CABLE_SW1][PORT1A].gpioNumLED = 234;
	CableLed[CABLE_SW1][PORT1B].gpioNumLED = 235;

	CableLed[CABLE_SW1][PORT2A].gpioNumA32Present = 236;
	CableLed[CABLE_SW1][PORT2A].gpioNumB9Present = 237;
	CableLed[CABLE_SW1][PORT2B].gpioNumA32Present = 238;
	CableLed[CABLE_SW1][PORT2B].gpioNumB9Present = 239;
	CableLed[CABLE_SW1][PORT2A].gpioNumPresent = 240;
	CableLed[CABLE_SW1][PORT2B].gpioNumPresent = 241;
	CableLed[CABLE_SW1][PORT2A].gpioNumLED = 242;
	CableLed[CABLE_SW1][PORT2B].gpioNumLED = 243;

	CableLed[CABLE_SW2][PORT1A].gpioNumA32Present = 244;
	CableLed[CABLE_SW2][PORT1A].gpioNumB9Present = 245;
	CableLed[CABLE_SW2][PORT1B].gpioNumA32Present = 246;
	CableLed[CABLE_SW2][PORT1B].gpioNumB9Present = 247;
	CableLed[CABLE_SW2][PORT1A].gpioNumPresent = 248;
	CableLed[CABLE_SW2][PORT1B].gpioNumPresent = 249;
	CableLed[CABLE_SW2][PORT1A].gpioNumLED = 250;
	CableLed[CABLE_SW2][PORT1B].gpioNumLED = 251;

	CableLed[CABLE_SW2][PORT2A].gpioNumA32Present = 252;
	CableLed[CABLE_SW2][PORT2A].gpioNumB9Present = 253;
	CableLed[CABLE_SW2][PORT2B].gpioNumA32Present = 254;
	CableLed[CABLE_SW2][PORT2B].gpioNumB9Present = 255;
	CableLed[CABLE_SW2][PORT2A].gpioNumPresent = 256;
	CableLed[CABLE_SW2][PORT2B].gpioNumPresent = 257;
	CableLed[CABLE_SW2][PORT2A].gpioNumLED = 258;
	CableLed[CABLE_SW2][PORT2B].gpioNumLED = 259;

	CableLed[CABLE_SW3][PORT1A].gpioNumA32Present = 260;
	CableLed[CABLE_SW3][PORT1A].gpioNumB9Present = 261;
	CableLed[CABLE_SW3][PORT1B].gpioNumA32Present = 262;
	CableLed[CABLE_SW3][PORT1B].gpioNumB9Present = 263;
	CableLed[CABLE_SW3][PORT1A].gpioNumPresent = 264;
	CableLed[CABLE_SW3][PORT1B].gpioNumPresent = 265;
	CableLed[CABLE_SW3][PORT1A].gpioNumLED = 266;
	CableLed[CABLE_SW3][PORT1B].gpioNumLED = 267;

	CableLed[CABLE_SW3][PORT2A].gpioNumA32Present = 268;
	CableLed[CABLE_SW3][PORT2A].gpioNumB9Present = 269;
	CableLed[CABLE_SW3][PORT2B].gpioNumA32Present = 270;
	CableLed[CABLE_SW3][PORT2B].gpioNumB9Present = 271;
	CableLed[CABLE_SW3][PORT2A].gpioNumPresent = 272;
	CableLed[CABLE_SW3][PORT2B].gpioNumPresent = 273;
	CableLed[CABLE_SW3][PORT2A].gpioNumLED = 274;
	CableLed[CABLE_SW3][PORT2B].gpioNumLED = 275;

	CableLed[CABLE_SW4][PORT1A].gpioNumA32Present = 276;
	CableLed[CABLE_SW4][PORT1A].gpioNumB9Present = 277;
	CableLed[CABLE_SW4][PORT1B].gpioNumA32Present = 278;
	CableLed[CABLE_SW4][PORT1B].gpioNumB9Present = 279;
	CableLed[CABLE_SW4][PORT1A].gpioNumPresent = 280;
	CableLed[CABLE_SW4][PORT1B].gpioNumPresent = 281;
	CableLed[CABLE_SW4][PORT1A].gpioNumLED = 282;
	CableLed[CABLE_SW4][PORT1B].gpioNumLED = 283;

	CableLed[CABLE_SW4][PORT2A].gpioNumA32Present = 284;
	CableLed[CABLE_SW4][PORT2A].gpioNumB9Present = 285;
	CableLed[CABLE_SW4][PORT2B].gpioNumA32Present = 286;
	CableLed[CABLE_SW4][PORT2B].gpioNumB9Present = 287;
	CableLed[CABLE_SW4][PORT2A].gpioNumPresent = 288;
	CableLed[CABLE_SW4][PORT2B].gpioNumPresent = 289;
	CableLed[CABLE_SW4][PORT2A].gpioNumLED = 290;
	CableLed[CABLE_SW4][PORT2B].gpioNumLED = 291;
}

void open_gpio()
{
	int i = 0;
	int j = 0;
	char buff_path[256] = "";

	for(i=0; i<MAX_CABLE_SW; i++) {
		for(j=0; j<MAX_CABLE_PORT; j++) {
			sprintf(buff_path, "echo %d > /sys/class/gpio/export", CableLed[i][j].gpioNumA32Present);
			system(buff_path);

			sprintf(buff_path, "echo %d > /sys/class/gpio/export", CableLed[i][j].gpioNumB9Present);
			system(buff_path);

			sprintf(buff_path, "echo %d > /sys/class/gpio/export", CableLed[i][j].gpioNumPresent);
			system(buff_path);

			sprintf(buff_path, "echo %d > /sys/class/gpio/export", CableLed[i][j].gpioNumLED);
			system(buff_path);

			sprintf(buff_path, "echo in > /sys/class/gpio/gpio%d/direction", CableLed[i][j].gpioNumA32Present);
			system(buff_path);

			sprintf(buff_path, "echo in > /sys/class/gpio/gpio%d/direction", CableLed[i][j].gpioNumB9Present);
			system(buff_path);

			sprintf(buff_path, "echo out > /sys/class/gpio/gpio%d/direction", CableLed[i][j].gpioNumPresent);
			system(buff_path);

			sprintf(buff_path, "echo out > /sys/class/gpio/gpio%d/direction", CableLed[i][j].gpioNumLED);
			system(buff_path);
		}
	}
}

int main(gint argc, gchar *argv[])
{
	init_cable_gpio_mapping();
	open_gpio();
	check_cable_status();
	return 0;
}
