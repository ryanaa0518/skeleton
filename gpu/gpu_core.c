#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <dirent.h>
#include <systemd/sd-bus.h>
#include <linux/i2c-dev-user.h>
#include <stdbool.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sdbus_property.h>

#define MAX_I2C_DEV_LEN 32
#define MBT_REG_CMD            0x5c
#define MBT_REG_DATA_KEPLER    0x5d
#define NV_CMD_GET_TEMP 0x02
#define NV_CMD_GET_GPU_INFORMATION    0x05
#define GPU_ACCESS_SUCCESS_RETURN 0x1f

#define TYPE_BOARD_PART_NUMBER 0x0
#define TYPE_SERIAL_NUMBER 0x2
#define TYPE_MARKETING_NAME 0x3

#define GPU_TEMP_PATH "/tmp/gpu"


#define MAX_GPU_NUM (8)
#define MAX_INFO_INDEX 16
#define MAX_INFO_LENGTH 64
#define PMBUS_DELAY usleep(400*1000)

enum {
	EM_GPU_DEVICE_1 = 0,
	EM_GPU_DEVICE_2,
	EM_GPU_DEVICE_3,
	EM_GPU_DEVICE_4,
	EM_GPU_DEVICE_5,
	EM_GPU_DEVICE_6,
	EM_GPU_DEVICE_7,
	EM_GPU_DEVICE_8,
};

struct gpu_data {
	bool temp_ready;
	__u8 temp;

	bool info_ready;
	unsigned char info_data[MAX_INFO_INDEX][MAX_INFO_LENGTH];
};

char info_string[MAX_INFO_INDEX][MAX_INFO_LENGTH] = {
	{"Board Part Number"},
	{""},
	{"Serial Number"},
	{"Marketing Name"},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
	{""},
};

struct gpu_data G_gpu_data[MAX_GPU_NUM];

typedef struct {
	__u8 bus_no;

	__u8 slave;

	__u8 device_index;

} gpu_device_mapping;

gpu_device_mapping gpu_device_bus[MAX_GPU_NUM] = {
	{28, 0x4d, EM_GPU_DEVICE_1},
	{29, 0x4d, EM_GPU_DEVICE_2},
	{30, 0x4d, EM_GPU_DEVICE_3},
	{31, 0x4d, EM_GPU_DEVICE_4},
	{32, 0x4d, EM_GPU_DEVICE_5},
	{33, 0x4d, EM_GPU_DEVICE_6},
	{34, 0x4d, EM_GPU_DEVICE_7},
	{35, 0x4d, EM_GPU_DEVICE_8},
};

static int internal_gpu_access(int bus, __u8 slave,__u8 *write_buf, __u8 *read_buf)
{
	int fd;
	char filename[MAX_I2C_DEV_LEN] = {0};
	int rc=-1;
	int retry_gpu = 5;
	unsigned char cmd_reg[4];

	memset(cmd_reg, 0x0, sizeof(cmd_reg));
	sprintf(filename,"/dev/i2c-%d",bus);
	fd = open(filename,O_RDWR);

	if (fd == -1) {
		fprintf(stderr, "Failed to open i2c device %s", filename);
		return rc;
	}
	rc = ioctl(fd,I2C_SLAVE,slave);
	if(rc < 0) {
		fprintf(stderr, "Failed to do iotcl I2C_SLAVE\n");
		goto error_smbus_access;
	}

	if(i2c_smbus_write_block_data(fd, MBT_REG_CMD, 4, write_buf) < 0) {
		goto error_smbus_access;
	}

	while(retry_gpu) {

		if (i2c_smbus_read_block_data(fd, MBT_REG_CMD, cmd_reg) != 4) {
			printf("Error: on bus %d reading from 0x5c",bus);
			goto error_smbus_access;
		}
		PMBUS_DELAY;
		if(cmd_reg[3] == GPU_ACCESS_SUCCESS_RETURN) {
			if (i2c_smbus_read_block_data(fd, MBT_REG_DATA_KEPLER, read_buf) == 4) { /*success get data*/
				close(fd);
				return 0;
			}
		} else {
			printf("read bus %d return 0x%x 0x%x 0x%x 0x%x, not in success state\n",bus ,cmd_reg[0], cmd_reg[1], cmd_reg[2], cmd_reg[3]);
		}
		retry_gpu--;
		PMBUS_DELAY;
	}
error_smbus_access:
	close(fd);
	return -1;
}

static int function_get_gpu_info(int index)
{

	unsigned char temp_writebuf[4] = {NV_CMD_GET_GPU_INFORMATION,0x0,0x0,0x80};
	unsigned char input_cmd_data[MAX_INFO_INDEX][2] = {
		{TYPE_BOARD_PART_NUMBER,24},
		{TYPE_SERIAL_NUMBER,16},
		{TYPE_MARKETING_NAME,24},
		{0xFF,0xFF}, //List of end
	};
	unsigned char temp_readbuf[MAX_INFO_INDEX][32];
	unsigned char read_times = 0;
	unsigned char cuurent_index=0;
	int rc=-1;
	int i,j;
	int memroy_index=0;
	memset(temp_readbuf, 0x0, sizeof(temp_readbuf));

	for(i=0; input_cmd_data[i][0]!=0xFF; i++) {
		read_times = input_cmd_data[i][1]/4;
		for(j=0; j<read_times; j++) {
			temp_writebuf[1]=input_cmd_data[i][0]; /* type*/
			temp_writebuf[2]=j; /* times*/
			rc = internal_gpu_access(gpu_device_bus[index].bus_no,
						 gpu_device_bus[index].slave,temp_writebuf,&temp_readbuf[i][j*4]);

			if(rc < 0) {
				fprintf(stderr, "failed to access gpu info index %d \n",index);
				G_gpu_data[gpu_device_bus[index].device_index].info_ready = 0;
				return rc;
			}

		}
		memroy_index = input_cmd_data[i][0];

		sprintf(&G_gpu_data[gpu_device_bus[index].device_index].info_data[memroy_index][0],"%s\0",&temp_readbuf[i][0]);
		printf("Success get the gpu info =%s \r\n",G_gpu_data[gpu_device_bus[index].device_index].info_data[memroy_index]);
	}
	G_gpu_data[gpu_device_bus[index].device_index].info_ready = 1;
#undef MAX_INFO_INDEX
	return 0;
}

int function_get_gpu_data(int index)
{

	unsigned char temp_writebuf[4] = {NV_CMD_GET_TEMP,0x0,0x0,0x80};
	unsigned char readbuf[4];
	int rc=0;
	char gpu_path[128];
	char sys_cmd[128];
	char gpu_info_node[256] = {0};
	int len=0;
	int i=0;
	FILE *fp;
	/*get gpu temp data*/
	rc = internal_gpu_access(gpu_device_bus[index].bus_no,gpu_device_bus[index].slave,temp_writebuf,readbuf);
	if(rc==0) {
		G_gpu_data[gpu_device_bus[index].device_index].temp_ready = 1;
		G_gpu_data[gpu_device_bus[index].device_index].temp = readbuf[1];
		/* write data to file */
		sprintf(gpu_path , "%s%s%d%s", GPU_TEMP_PATH, "/gpu", gpu_device_bus[index].device_index+1,"_temp");
		sprintf(sys_cmd, "echo %d > %s", readbuf[1], gpu_path);
		system(sys_cmd);
	} else {
		if(G_gpu_data[gpu_device_bus[index].device_index].temp_ready) { /*if previous is ok*/
			sprintf(gpu_path , "%s%s%d%s", GPU_TEMP_PATH, "/gpu", gpu_device_bus[index].device_index+1,"_temp");
			sprintf(sys_cmd, "echo %d > %s", -1, gpu_path);
			system(sys_cmd);
		}
		G_gpu_data[gpu_device_bus[index].device_index].temp_ready = 0;
		return rc;
	}
	/*get gpu info data */
	if(!G_gpu_data[gpu_device_bus[index].device_index].info_ready) {
		rc=function_get_gpu_info(index);
		if(rc==0) {
			len = snprintf(gpu_info_node, sizeof(gpu_info_node), "%s%d%s",
				       "/org/openbmc/sensors/gpu/gpu",gpu_device_bus[index].device_index+1,"_temp");
			set_dbus_property(gpu_info_node , "Board Part Number", "s", (void *) G_gpu_data[gpu_device_bus[index].device_index].info_data[TYPE_BOARD_PART_NUMBER]);
			set_dbus_property(gpu_info_node , "Serial Number", "s", (void *)G_gpu_data[gpu_device_bus[index].device_index].info_data[TYPE_SERIAL_NUMBER]);
			set_dbus_property(gpu_info_node , "Marketing Name", "s", (void *)G_gpu_data[gpu_device_bus[index].device_index].info_data[TYPE_MARKETING_NAME]);
		} else
			fprintf(stderr, "failed to set_gpu_info_propetry index %d \n",index);
	}
	return rc;
}

void gpu_data_scan()
{
	/* init the global data */
	memset(G_gpu_data, 0x0, sizeof(G_gpu_data));
	int i =0;
	struct stat st = {0};
	char gpu_path[128];
	FILE *fp;
	/* create the file patch for dbus usage*/
	/* check if directory is existed */
	if (stat(GPU_TEMP_PATH, &st) == -1) {
		mkdir(GPU_TEMP_PATH, 0777);
	}
	for(i=0; i<MAX_GPU_NUM; i++) {
		sprintf(gpu_path , "%s%s%d%s", GPU_TEMP_PATH, "/gpu", i+1,"_temp");
		if( access( gpu_path, F_OK ) != -1 ) {
			fprintf(stderr,"Error:[%s] opening:[%s] , existed \n",gpu_path);
			break;
		} else {
			fp = fopen(gpu_path,"w");
			if(fp == NULL) {
				fprintf(stderr,"Error:[%s] opening:[%s]\n",strerror(errno),gpu_path);
				return;
			}
			fprintf(fp, "%d",-1);
			fclose(fp);
		}
	}
	while(1) {
		for(i=0; i<MAX_GPU_NUM; i++) {
			function_get_gpu_data(i);
			sleep(1);
		}
	}
}

int
main(void)
{
	gpu_data_scan();
	return 0;
}


