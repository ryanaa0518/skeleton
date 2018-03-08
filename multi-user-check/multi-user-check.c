#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define MULTI_USER_STATUS_DEAD 3

int multi_user_check()
{
    int stat = 0;
    char cmd[256];

    //Check firmware update complete
    while (1) {
        sprintf(cmd, "systemctl status multi-user.target");
        stat = WEXITSTATUS(system(cmd));

        if (stat == MULTI_USER_STATUS_DEAD) {
            //Multi-user target is dead, doing re-execute init daemon
            printf("Multi User Target dead, start to re-execute init daemon\n");
            system("/sbin/init u; sleep 20; /sbin/init 3");
        }

        sleep(10);
    }
}

int main(void)
{
    multi_user_check();
    return 0;
}
