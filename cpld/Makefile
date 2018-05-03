

CFLAGS  = -O2 -Wall -I.
LDFLAGS	= -lrt 
OBJS	= main.o lattice.o ast-jtag.o
EXE	= cpld

CC      = $(CROSS_COMPILE)gcc

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@ -I.

$(EXE): $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@ -I.
install:
	mkdir -p $(DESTDIR)/usr/sbin
	install cpld.exe $(DESTDIR)/usr/sbin

#clean:
#	rm -f $(OBJS) $(EXE) *.o *.d libflash/test/test_flash libflash/test/*.o
