#!/usr/bin/python -u

import getopt
import sys
from obmc.events import Event
from obmc.events import EventManager

event_manager = EventManager()

def main():
    try:
        opts, args=getopt.getopt(sys.argv[1:], "I:E:", ["INFO=", "ERROR="])
    except getopt.GetoptError as err:
        #print ("getopt error")
        sys.exit(2)

    if len(opts) < 1:
        #print ("no opts")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-I", "--INFO"):
            #print "EVENT SEVERITY:INFO, Desc:%s" % arg
            EVT_SEV = Event.SEVERITY_INFO

        elif opt in ("-E", "--ERROR"):
            #print "EVENT SEVERITY:ERROR, Desc:%s" % arg
            EVT_SEV = Event.SEVERITY_ERR

        else:
            assert False, "unhandled option"
            sys.exit(2)

    desc = arg
    log = Event(EVT_SEV, desc)
    event_manager.add_log(log)

if __name__ == '__main__':
    main()

