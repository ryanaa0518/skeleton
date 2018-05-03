#ifdef INST
#ifeq ("$(origin INST)", "command line")
#INSTALL_DIR := $(INST)
#endif
#endif

CFLAGS += -Wall
OBJS	= main.o lattice.o ast-jtag.o
EXE	= cpld
#INSTALL_DIR = /usr/sbin

#CC      = $(CROSS_COMPILE)gcc

%.o : %.c:
	$(CC) $(CFLAGS) -c $< -o $@ -I.

$(EXE): $(OBJS)
	$(CC) $(CFLAGS) $" -o $@ -I.

clean:
	rm -f $(EXE) $(OBJS)

#install:
#	cp $(EXE) $(DESTDIR)
#	cp $(EXE) $(INSTALL_DIR)
