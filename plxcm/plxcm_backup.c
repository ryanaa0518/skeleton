/*
        buildCommandList builds list of commands to send to PLX, accordingly to the datasheet.
        This command list does not enable FABRIC MODE.

                       BITS  DESCRIPTION
        +------------+-----+---------------------------------------------------------------------------+
        | CMD BYTE 1 | 7:3 | RESERVED - should be cleared                                              |
        |            +-----+---------------------------------------------------------------------------+
        |            | 2:0 | COMMAND:                                                                  |
        |            |     |    011b = write register                                                  |
        |            |     |    100b = read register                                                   |
        +------------+-----+---------------------------------------------------------------------------+
        | CMD BYTE 2 | 7   | RESERVED - should be cleared                                              |
        |            +-----+---------------------------------------------------------------------------+
        |            | 6:5 | ACCESS MODE:                                                              |
        |            |     |    00b = transparent ports                                                |
        |            |     |    01b = NTx Port Link Interface                                          |
        |            |     |    10b = NTx Port Virtual Interface                                       |
        |            |     |    11b = RESERVED                                                         |
        |            +-----+---------------------------------------------------------------------------+
        |            | 4:2 | STATION SELECT (when ACCESS MODE == 00b):                                 |
        |            |     |    000b = station 0                                                       |
        |            |     |    001b = station 1                                                       |
        |            |     |    010b = station 2                                                       |
        |            |     |    all other encodings are RESERVED                                       |
        |            +-----+---------------------------------------------------------------------------+
        |            | 1:0 | PORT SELECT [2:1]                                                         |
        +------------+-----+---------------------------------------------------------------------------+
        | CMD BYTE 3 | 7   | PORT SELECT [0]                                                           |
        |            |     | when ACCESS MODE == 00b:                                                  |
        |            |     |    000b = port 0 of the station                                           |
        |            |     |    001b = port 1 of the station                                           |
        |            |     |    010b = port 2 of the station                                           |
        |            |     |    011b = port 3 of the station                                           |
        |            |     |                                                                           | 
        |            |     | when ACCESS MODE == 01b or 10b:                                           |
        |            |     |    000b = NT0 port                                                        |
        |            |     |    001b = NT1 port                                                        |
        |            |     |                                                                           | 
        |            |     | all other encodings are RESERVED                                          |
        |            +-----+---------------------------------------------------------------------------+
        |            | 6   | RESERVED - should be cleared                                              |
        |            +-----+---------------------------------------------------------------------------+
        |            | 5:2 | BYTE ENABLES                                                              |
        |            |     |                                                                           | 
        |            |     | bit   description                                                         |
        |            |     | 2     byte enable for byte 0 (PEX 8750 register bits [7:0])               |
        |            |     | 3     byte enable for byte 1 (PEX 8750 register bits [15:8]               |
        |            |     | 4     byte enable for byte 2 (PEX 8750 register bits [23:16])             |
        |            |     | 5     byte enable for byte 3 (PEX 8750 register bits [31:24])             |
        |            |     |                                                                           | 
        |            |     | 0 = corresponding PEX 8750 register byte will not be modified             |
        |            |     | 1 = corresponding PEX 8750 register byte will be modified                 |
        |            +-----+---------------------------------------------------------------------------+
        |            | 1:0 | PEX 8750 REGISTER ADDRESS - bits [11:10]                                  |
        +------------+-----+---------------------------------------------------------------------------+
        | CMD BYTE 4 | 7:0 | PEX 8750 REGISTER ADDRESS - bits [9:2]                                    |
        |            |     |                                                                           | 
        |            |     | all register addresses are DWORD-aligned. therefore, address bits [1:0]   |
        |            |     | are implicitly cleared (0), and then internally incremented for sucessive |  
        |            |     | I2C byte writes/reads                                                     |
        +------------+-----+---------------------------------------------------------------------------+
     
*/       

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
//for system call 
#include <stdlib.h> 

#define MAX_I2C_DEV_LEN 32
#define GPU_ACCESS_SUCCESS_RETURN 0x1f
#define MAX_PEX_NUM (4)

#define PEX_TEMP_PATH "/tmp/pex"
#define PEX_SERIAL_LEN (8)
#define PEX_UDID_LEN (17)
#define PEX_SMBUS_BLOCK_WRITE_CMD (0xBE)

#define VERSION   "0.01" 

enum {
	EM_PEX_DEVICE_1 = 0,
	EM_PEX_DEVICE_2,
	EM_PEX_DEVICE_3,
	EM_PEX_DEVICE_4,
	EM_PEX_DEVICE_5,
	EM_PEX_DEVICE_6,
	EM_PEX_DEVICE_7,
	EM_PEX_DEVICE_8,
};

enum {
	EM_PEX_CMD_TEMP_DISABLE_CTL = 0,
	EM_PEX_CMD_TEMP_ENABLE_CTL,
	EM_PEX_CMD_TEMP_READ,
	EM_PEX_CMD_UPPER_SERIAL_READ,
	EM_PEX_CMD_LOWER_SERIAL_READ,
	EM_PEX_CMD_ENABLE_SMBUS,
	EM_PEX_CMD_DISABLE_SMBUS,
	EM_PEX_CMD_UDID_READ,
	EM_PEX_CMD_MAX
};

typedef struct {
	__u32 serial_count;
	__u8 serial_data[PEX_SERIAL_LEN];
} pex_device_serial;

typedef struct {
	__u32 udid_count;
	__u8 udid_sdbus_flag;
	__u8 udid_data[PEX_UDID_LEN];
} pex_device_udid;


typedef struct {
	__u8 bus_no;

	__u8 slave;  //i2c address

	__u8 device_index;

	__u8 sensor_number;

	__u8 smbus_slave;
	pex_device_serial serial;
	pex_device_udid  udid;
} pex_device_mapping;

pex_device_mapping pex_device_bus[MAX_PEX_NUM] = {
	{16, 0x5d, EM_PEX_DEVICE_1, 0x37, 0x61, {0, {0}}, {0, 0, {0}} },
	{17, 0x5d, EM_PEX_DEVICE_2, 0x38, 0x61, {0, {0}}, {0, 0, {0}} },
	{18, 0x5d, EM_PEX_DEVICE_3, 0x39, 0x61, {0, {0}}, {0, 0, {0}} },
	{19, 0x5d, EM_PEX_DEVICE_4, 0x3A, 0x61, {0, {0}}, {0, 0, {0}} },
};

typedef struct {
	int len;
	__u8 data[256];
} i2c_cmd_data;

typedef struct {
	int cmd;
	i2c_cmd_data write_cmd;
	i2c_cmd_data read_cmd;
} pex_device_i2c_cmd;


pex_device_i2c_cmd pex_device_cmd_tab[EM_PEX_CMD_MAX] = {
	{
		EM_PEX_CMD_TEMP_DISABLE_CTL,
		{8, {0x3, 0x0, 0x3e, 0xeb, 0x00, 0x00, 0x00, 0x00}},
		{-1,{0x0}}
	},
	{ 
		EM_PEX_CMD_TEMP_ENABLE_CTL,
		{8, {0x3, 0x0, 0x3e, 0xeb, 0x00, 0x00, 0x00, 0x80}},
		{-1,{0x0}}
	},
	{
		EM_PEX_CMD_TEMP_ENABLE_CTL,
		{4, {0x4, 0x0, 0x3e, 0xeb}},
		{4, {0x0}}
	},
	{
		EM_PEX_CMD_LOWER_SERIAL_READ,
		{4, {0x4, 0x0, 0x3c, 0x41}},
		{4, {0x0}}
	},
	{
		EM_PEX_CMD_UPPER_SERIAL_READ,
		{4, {0x4, 0x0, 0x3c, 0x42}},
		{4, {0x0}}
	},
	{
		EM_PEX_CMD_ENABLE_SMBUS,
		{8, {0x3, 0x0, 0x3c, 0xb2, 0x01, 0x70, 0x62, 0x1}},
		{-1,{0x0}}
	},
	{
		EM_PEX_CMD_DISABLE_SMBUS,
		{8, {0x3, 0x0, 0x3c, 0xb2, 0x01, 0x70, 0x62, 0x0}},
		{-1,{0x0}}
	},
	{
		EM_PEX_CMD_DISABLE_SMBUS,
		{1, {0x3}},
		{17,{0x0}}
	},
};


#define PMBUS_DELAY usleep(400*1000)
#define I2C_CLIENT_PEC          0x04    /* Use Packet Error Checking */
#define I2C_M_RECV_LEN          0x0400  /* length will be first received byte */

static int g_use_pec = 0;

static int i2c_io(int fd, int slave_addr, int write_len, __u8 *write_data_bytes, int read_len, __u8 *read_data_bytes)
{
	struct i2c_rdwr_ioctl_data data;
	struct i2c_msg msg[2];
	int n_msg = 0;
	int rc;
	int i;

	memset(&msg, 0, sizeof(msg));

	if (write_len > 0) {
		printf("\r\n Write :");	
		msg[n_msg].addr = slave_addr;
		printf("\r\n msg[n_msg].addr : 0x%x ,", msg[n_msg].addr);
		msg[n_msg].flags = (g_use_pec) ? I2C_CLIENT_PEC : 0;
		printf(" msg[n_msg].flags :   0x%x ,",msg[n_msg].flags);
		msg[n_msg].len = write_len ;
		printf(" msg[n_msg].len :     0x%x ,",msg[n_msg].len);
		msg[n_msg].buf = write_data_bytes;
                
    printf(" msg[n_msg].buf :");
    for(i=0 ;i <msg[n_msg].len ;i ++)
    {
    	printf("0x%x ", msg[n_msg].buf[i]);
    } 
    printf("\r\n");
		n_msg++;
	}

	if (read_len>=0) {
                printf("\r\n Read :");
		msg[n_msg].addr = slave_addr;
    printf("\r\n msg[n_msg].addr : 0x%x ,",msg[n_msg].addr);
		msg[n_msg].flags = I2C_M_RD
				   | ((g_use_pec) ? I2C_CLIENT_PEC : 0)
				   | ((read_len == 0) ? I2C_M_RECV_LEN : 0);
		/*
		 * In case of g_n_read is 0, block length will be added by
		 * the underlying bus driver.
		 */
    printf(" msg[n_msg].flags : 0x%x ,",msg[n_msg].flags);
		msg[n_msg].len = (read_len) ? read_len : 256;
    printf(" msg[n_msg].len :   0x%x ,", msg[n_msg].len);
		msg[n_msg].buf = read_data_bytes ;
 
		n_msg++;
	}
        
	data.msgs = msg;
	data.nmsgs = n_msg;

	rc = ioctl(fd, I2C_RDWR, &data);
	if (rc < 0) {
		printf("Failed to do raw io\n");
		return -1;
	}
	
	printf(" msg[n_msg-1].buf :");
		
	//ryan: after the read , print the read message
	for(i=0 ;i <msg[n_msg-1].len ;i ++)
	{
	        printf("0x%02x ", msg[n_msg-1].buf[i]);
	}
  
  printf("\r\n\r\n");            	
	return 0;
	
}

static i2c_raw_access(int i2c_bus, int i2c_addr,int write_len, __u8 *write_data_bytes, int read_len, __u8 *read_data_bytes)
{
	int fd;
	char filename[MAX_I2C_DEV_LEN] = {0};
	int rc=-1;
	int retry_gpu = 5;
	int count = 0;
	int r_count = 0;
	int i;

	sprintf(filename,"/dev/i2c-%d",i2c_bus);
	fd = open(filename,O_RDWR);

	if (fd == -1) {
		fprintf(stderr, "Failed to open i2c device %s, error:%s", filename, strerror(errno));
		return rc;
	}

	rc = ioctl(fd,I2C_SLAVE,i2c_addr);
	if(rc < 0) {
		fprintf(stderr, "Failed to do iotcl I2C_SLAVE, error:%s\n", strerror(errno));
		close(fd);
		return rc;
	}

	if (read_len>0)
		memset(read_data_bytes, 0x0, read_len);

	rc = i2c_io(fd, i2c_addr, write_len, write_data_bytes, read_len, read_data_bytes);

	close(fd);

	return rc;

}




//add by ryan

int function_write_reg_data(int pex_idx,int port_id ,__u16 reg,__u32 data)
{
	pex_device_i2c_cmd *i2c_cmd;
	int i2c_bus;
	int i2c_addr;
	int ret;
	int i,station,port;
	char *rx_data;
	int rx_len = 0;
	unsigned int temp_sensor_data = 0;
	double real_temp_data = 0.0;
	int rc=-1;

	i2c_bus = pex_device_bus[pex_idx].bus_no;
	i2c_addr = pex_device_bus[pex_idx].slave;

	//printf("\r\n reg : 0x%x \r\n",reg);
	//printf("\r\n port_id : 0x%x \r\n",port_id);
	//printf("\r\n data : 0x%x \r\n",data);
	station = (port_id>>2)  ;
	port = port_id & 3 ;
	
		
	//EM_PEX_CMD_TEMP_READ : 2
	i2c_cmd = &pex_device_cmd_tab[EM_PEX_CMD_TEMP_DISABLE_CTL];	
	
	i2c_cmd->write_cmd.data[0]= 0x03; //write command
	i2c_cmd->write_cmd.data[1]= ((station&7)<<2) | ((port>>1)&3); //Non-Fabric Mode
	
	i2c_cmd->write_cmd.data[2]= (port&1)<<7 | 0x3c | ((reg>>10) & 3);
	//printf("\r\n i2c_cmd->write_cmd.data[2] : %x \r\n",i2c_cmd->write_cmd.data[2]);
	i2c_cmd->write_cmd.data[3]= (reg>>2)&0xff;
	//printf("\r\n i2c_cmd->write_cmd.data[3] : %x \r\n",i2c_cmd->write_cmd.data[3]);
	
	//data byte ; take care the byte order !!
	i2c_cmd->write_cmd.data[4]= ((data >>24)& 0xff);
	//printf("\r\n i2c_cmd->write_cmd.data[4] : %x \r\n",i2c_cmd->write_cmd.data[4]);
	
	i2c_cmd->write_cmd.data[5]= ((data >>16)& 0xff);
	//printf("\r\n i2c_cmd->write_cmd.data[5] : %x \r\n",i2c_cmd->write_cmd.data[5]);

	i2c_cmd->write_cmd.data[6]= ((data >>8)& 0xff);
	//printf("\r\n i2c_cmd->write_cmd.data[6] : %x \r\n",i2c_cmd->write_cmd.data[6]);
	
	i2c_cmd->write_cmd.data[7]= (data & 0xff);
	//printf("\r\n i2c_cmd->write_cmd.data[7] : %x \r\n",i2c_cmd->write_cmd.data[7]);
	
				
	ret = i2c_raw_access(i2c_bus, i2c_addr, i2c_cmd->write_cmd.len,
			     i2c_cmd->write_cmd.data, i2c_cmd->read_cmd.len, i2c_cmd->read_cmd.data);
	if (ret < 0) {
		printf("\r\n-----Fail to get thd data-----\r\n");
	}


}


int function_read_reg_data(int pex_idx ,int port_id ,__u16 reg)
{
	pex_device_i2c_cmd *i2c_cmd;
	int i2c_bus;
	int i2c_addr;
	int ret;
	int i,station,port;
	char *rx_data;
	int rx_len = 0;
	unsigned int temp_sensor_data = 0;
	double real_temp_data = 0.0;
	int rc=-1;
	char shell_cmd[128]="";
	__u32 regData= 0x00000000;

	i2c_bus = pex_device_bus[pex_idx].bus_no;
	i2c_addr = pex_device_bus[pex_idx].slave;

	//printf("\r\n reg : 0x%x \r\n",reg);
	//printf("\r\n port_id : 0x%x \r\n",port_id);
	station = (port_id>>2)  ;
	port = port_id & 3 ;
	
		
	//EM_PEX_CMD_TEMP_READ : 2
	i2c_cmd = &pex_device_cmd_tab[EM_PEX_CMD_TEMP_READ];	
	
	i2c_cmd->write_cmd.data[1]= ((station&7)<<2) | ((port>>1)&3); //Non-Fabric Mode	
	i2c_cmd->write_cmd.data[2]= (port&1)<<7 | 0x3c | ((reg>>10) & 3);
	//printf("\r\n i2c_cmd->write_cmd.data[2] : %x \r\n",i2c_cmd->write_cmd.data[2]);
	i2c_cmd->write_cmd.data[3]= (reg>>2)&0xff;
	//printf("\r\n i2c_cmd->write_cmd.data[3] : %x \r\n",i2c_cmd->write_cmd.data[3]);
			
	ret = i2c_raw_access(i2c_bus, i2c_addr, i2c_cmd->write_cmd.len,
			     i2c_cmd->write_cmd.data, i2c_cmd->read_cmd.len, i2c_cmd->read_cmd.data);
	if (ret < 0) {
		printf("\r\n-----Fail to get thd data-----\r\n");
	}


#if 1
//save the reg data in file system

	sprintf (shell_cmd, "mkdir /tmp/pex/%d/",pex_idx);
	system(shell_cmd);
	
	sprintf (shell_cmd, "mkdir /tmp/pex/%d/%d",pex_idx,port_id);
	system(shell_cmd);
		
	sprintf (shell_cmd, "touch /tmp/pex/%d/%d/0x%08x",pex_idx,port_id,reg);
	system(shell_cmd);
		
	regData = ((i2c_cmd->read_cmd.data[0]) << 24) |
						((i2c_cmd->read_cmd.data[1]) << 16) |
						((i2c_cmd->read_cmd.data[2]) << 8) |
						(i2c_cmd->read_cmd.data[3]);

	
	sprintf (shell_cmd, "echo 0x%08x > /tmp/pex/%d/%d/0x%08x",regData,pex_idx,port_id,reg);
	system(shell_cmd);
		
#endif

}	



void usage() {
	printf("=================================================\r\n");
	printf("The plxcm usage:\r\n");
	printf("=================================================\r\n");
  printf("\n version : %s \n", VERSION);
  printf("Usage: plxcm [-d device_id] [-p port_id] [-a address]  [-r|-w value] \n");
  printf("       -d : device id \n");
  printf("       -p : assign port \n");
  printf("       -a : assign address \n");
  printf("       -r : read  \n");
  printf("       -w  [value]:  write value   \n");  	
	printf("   such as  plxcm.exe -d 1 -p 0 -a 0xbac -r 1 \r\n");
	printf("   such as  plxcm.exe -d 1 -p 0 -a 0x80  -w 0xff  \r\n");
	printf("   such as  plxcm.exe -d 1 -f /var/wcs/home/eeprom_9797.bin -e 0 ; read eeprom\r\n");	
	printf("   such as  plxcm.exe -d 1 -f /var/wcs/home/eeprom_9797.bin -e 1 ; write eeprom \r\n");	
	printf("=================================================\r\n");
	printf("Device Id List\r\n");
	printf("-d = 0 :  16, 0x5d, EM_PEX_DEVICE_1 \r\n");
	printf("-d = 1 :  17, 0x5d, EM_PEX_DEVICE_2 \r\n");
	printf("-d = 2 :  18, 0x5d, EM_PEX_DEVICE_3 \r\n");
	printf("-d = 3 :  19, 0x5d, EM_PEX_DEVICE_4 \r\n");
	
	
}

	
#define CTRL_WRITE_4BYTES  0b010
#define CTRL_SET_WENABLE   0b110
#define BUFFER_REG         0x264
#define STATUS_CTRL_REG    0x260
	
int write_prepare(int pex_idx,int port_id ,int addr ,__u32 data)
{
	__u32 cmd1 ,cmd0 ;
	
	
	cmd0 = (CTRL_SET_WENABLE <<13);
  cmd1 = (CTRL_WRITE_4BYTES <<13) | (addr & 0xFFF);
  
	function_write_reg_data( pex_idx, port_id , BUFFER_REG, data);
	function_write_reg_data( pex_idx, port_id , STATUS_CTRL_REG, cmd0);
	function_write_reg_data( pex_idx, port_id , STATUS_CTRL_REG, cmd1);

}



int writeEeprom(int pex_idx,int port_id ,char* eepromFile)
{
	int size;
	FILE *fd;
	char buffer[512];
	int padding,datalen,addr;
	__u32 d;
	
	
	//sprintf(filename,"%s",eepromFile);
	printf("\r\n------eepromFile : %s-----\r\n" , &eepromFile );
	//fd = open(eepromFile,O_RDWR);
	fd = fopen(eepromFile,"rb");

	if (fd == NULL) {
		printf("\r\nFail to open the eepromFile \r\n");
		return 0;
	}
	
	fseek(fd, 0, SEEK_END); // seek to end of file
	size = ftell(fd); // get current file pointer
	fseek(fd, 0, SEEK_SET); // seek back to beginning of file

	printf("\r\n--size : %d --\r\n",size);
  fread(buffer,sizeof(char),size,fd);

  //write eeprom settings
	datalen = size/4;
	printf("\r\n datalen : %d \r\n",datalen);
		
	padding = 4-(size%4);
	printf("\r\n padding : %d \r\n",padding);
	

	for(addr= 0 ;addr <= datalen;addr++)
	{
		if((addr == datalen) && (padding !=0 ))
		{	
			if(padding == 3)
			{
				d = buffer[addr*4 + 0] | (0xff << 8) | (0xff << 16) | (0xff << 24);
			}
			else if (padding ==2 )	
			{
				d = buffer[addr*4 + 0] | (buffer[addr*4 + 1] << 8) | (0xff << 16) | (0xff << 24);
			}	
			else if (padding ==1 )	
			{
				d = buffer[addr*4 + 0] | (buffer[addr*4 + 1] << 8) | (buffer[addr*4 + 2] << 16) | (0xff << 24);
			}				
		}
		else
		{		
   		d = buffer[addr*4 + 0] | (buffer[addr*4 + 1] << 8) | (buffer[addr*4 + 2] << 16) | (buffer[addr*4 + 3] << 24);
		}  
  	printf("\r\n---count : %d ,data:%x ---\r\n", addr, d);
    write_prepare(pex_idx,port_id,addr, d);
	}
	
	
	
	  
  fclose(fd);

}


int main(int argc, char** argv)
{
	int i;
	int devArg,portArg,regArg,eepromAction;
	__u32 regData;
	char eepromFile[100]="";
					
	//if the input parameter is fewer , show warning message
	if(argc <4)
	{
		usage();
		return 0;
	}
	
	for(i=0;i<argc;i++)
	{
		//printf("\r\nargv[%d]: %s\r\n",i,argv[i]);	
	}
	  
	while (argc > 2) {
    char* const opt = argv[1];
    //printf("\r\nargv[1] : %s \r\n" ,argv[1]);
    
    
    if (opt[0] != '-') usage();
    ////printf("\r\n opt[0] :%s  , opt[1] :%s\r\n",&opt[0],&opt[1]);
    
    switch (opt[1]) {
    	
				case 'd': { // specify device id
					//printf("\r\nSetting the device id:");
			
					if (sscanf(argv[2], "%d", &devArg) != 1) {
						usage();
					}
				
				//printf("%d \r\n",devArg);
				argv=argv+2; 
				argc=argc-2;
				break;
				}
				
				case 'p': { // specify port number
					//printf("\r\nSetting the port:");
			
					if (sscanf(argv[2], "%d", &portArg) != 1) {
						usage();
					}
				
				//printf("%d \r\n",portArg);
				argv=argv+2; 
				argc=argc-2;
				break;
				}
				
				case 'a': { // specify the register address
			
					if (sscanf(argv[2], "%x", &regArg) != 1) {
						usage();
					}
				
				//printf("0x%x \r\n",regArg);
				argv=argv+2; 
				argc=argc-2;
				break;
				}

				case 'r': { // read the register	
	
				function_read_reg_data(devArg,portArg,regArg);
				argv=argv+2; 
				argc=argc-2;
				break;
				}

				case 'w': { // write the register
	
					if (sscanf(argv[2], "%x", &regData) != 1) {
						usage();
					}
				
					//printf("%x \r\n",regData);
				
				function_write_reg_data(devArg,portArg,regArg,regData);
				argv=argv+2; 
				argc=argc-2;
				break;
				}				
				
				case 'f': { // handle the eeprom file
					//printf("\r\nReading the register\r\n");				
	
					if (sscanf(argv[2], "%s", &eepromFile) != 1) {
						usage();
					}
					
					printf("\r\n1.eeprom file name :%s\r\n", &eepromFile);	
				argv=argv+2; 
				argc=argc-2;
				break;
				}				

				case 'e': { // handle the eeprom
					//printf("\r\nReading the register\r\n");				
	
					if (sscanf(argv[2], "%d", &eepromAction) != 1) {
						usage();
					}
								
					if (eepromAction == 0)  //read the eeprom to file
					{
							printf("\r\nread the eeprom to file \r\n");
					}
					else if(eepromAction == 1) //write the eeprom to file				
					{ 
						printf("\r\n2.eeprom file name :%s\r\n", &eepromFile);						
							writeEeprom(devArg,portArg,eepromFile);
							printf("\r\nwrite the eeprom to file \r\n");
					}
					else
					{
						usage();
					}		
						
					argv=argv+2; 
					argc=argc-2;
				break;
				}				

		    default: {
		      usage();
		      return 0;
		    }

  	}
	}	
	return 0;
}


