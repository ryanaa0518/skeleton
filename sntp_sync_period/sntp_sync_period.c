#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

#define NTP_CONF_PATH "/etc/systemd/network/sntpaddress"
#define NTP_SYNC_PERIOD 60 // (3600)1hr
#define NTP_SYNC_SUCCESS 0
#define NTP_SENSOR_NUM 0x81
#define NTP_SENSOR_TYPE 0x12
#define NTP_EVENT_TYPE 0x71
#define EVD_SYNC_TIME 0x1
#define EVD_SYNC_TIME_FAIL 0x3
#define NOT_SYNCED 0
#define IS_SYNCED 1

int sntp_sync()
{
    FILE* fp;
    int ip[4], temp_ip[4]={-1,-1,-1,-1};
    int flag = NOT_SYNCED;
    char cmd[256];
    int stat = 0;
    int last_sync_stat = -1;
    int assert_ntp_failed = 0;
    struct timeval tv_pre, tv_cur;
    int timeshift;
    int IS_FROUND = 1;

    while (1) {
        fp = fopen(NTP_CONF_PATH, "r");
        if (fp == NULL) {

            if(last_sync_stat != 1){
                /* Log the sync result event when sync cmd is diff stat*/
                sprintf(cmd, "/usr/bin/python /usr/sbin/event.py --ERROR='Timestamp Synced with NTP server failed'");
                system(cmd);
                last_sync_stat = 1;
            }

            sleep(NTP_SYNC_PERIOD);
            continue;
        }

        fscanf(fp, "%d.%d.%d.%d", &ip[0], &ip[1], &ip[2], &ip[3]);
        fclose(fp);

        if((ip[0] != temp_ip[0]) || (ip[1] != temp_ip[1]) ||
          (ip[2] != temp_ip[2]) || (ip[3] != temp_ip[3])){
            flag = NOT_SYNCED;
        }

        int idx;
        for(idx=0; idx<4; idx++){
            temp_ip[idx] = ip[idx];
        }

        if(IS_FROUND){
            flag = NOT_SYNCED;
            IS_FROUND = 0;
        }

        if(flag == IS_SYNCED){
            sleep(NTP_SYNC_PERIOD);
            continue;
        }


        /* Get current timestamp */
        gettimeofday(&tv_pre,NULL);

        /* Execute sntp sync command */
        sprintf(cmd, "/usr/sbin/sntp -d -S %d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
        stat = WEXITSTATUS(system(cmd));

        if (stat == NTP_SYNC_SUCCESS) {

            flag = IS_SYNCED;

            if(stat != last_sync_stat){
                /* Log the sync result event when sync cmd is diff stat*/
                sprintf(cmd, "/usr/bin/python /usr/sbin/event.py --INFO='Timestamp Synced with NTP server successed'");
                system(cmd);
            }

            if (assert_ntp_failed) {
                printf("De-Assert NTP sync failed\n");
                /**
                 **/
                assert_ntp_failed = 0;
            } else {
                gettimeofday(&tv_cur,NULL);
                timeshift = abs(tv_cur.tv_sec - tv_pre.tv_sec);
                /* If the timestamp diff is more than 1 second, we should log the synced success event */
                if (timeshift > 1) {
                    printf("Synced with NTP server\n");
                    /**
                     **/
                }
            }
        } else {

            flag = NOT_SYNCED;

            if(stat != last_sync_stat){
                /* Log the sync result event when sync cmd is diff stat*/
                sprintf(cmd, "/usr/bin/python /usr/sbin/event.py --ERROR='Timestamp Synced with NTP server failed'");
                system(cmd);
            }

            if (!assert_ntp_failed) {
                printf("Assert NTP sync failed\n");
                /**
                 **/
                assert_ntp_failed = 1;
            }
        }

        last_sync_stat = stat;
        sleep(NTP_SYNC_PERIOD);
    }
}

int main(void)
{
    sntp_sync();
    return 0;
}
