# SerialUtils.py

import serial as ser
import threading
import time
import logging as lg
import RomadsUtils as RU
#import wx

reload(lg)
reload(RU)

logger = lg.getLogger()
logger.setLevel(lg.DEBUG)
logger.addHandler(lg.NullHandler())

SLEEPTIME = 0.01
TIMEOUT = 1

class Port_Object():
    def __init__(self, port_index, port_name, port_path):
        self.port_index = port_index
        self.port_name = port_name
        self.port_path = port_path

def NULL_PORT():
    return Port_Object(0, 'None', 'None')

class Port_Rcvr(threading.Thread):
    def __init__(self, serPort, gui):
        threading.Thread.__init__(self)
        self.serPort = serPort
        self.gui = gui
        self.evt_run = threading.Event()
        
        self.serPort.flushInput()
        self.serPort.flushOutput()

        self.evt_run.set() # set the evt_run flag
        
    ## end __init__
    
    def run(self):
        while self.evt_run.is_set():

            bytes_waiting = self.serPort.inWaiting()
            # Print in hex every byte received
            if bytes_waiting > 0:
                print 'Found byte:', hex(ord(self.serPort.read(1)))
            else:
                time.sleep(SLEEPTIME)
    ## end run 
    
    def close(self):
        logger.debug('closing port receiver thread')
        self.evt_run.clear()
        
    ## end close 

class TVAC_Port_Rcvr(Port_Rcvr):
    def __init__(self, serPort, echo_q, gui):
        Port_Rcvr.__init__(self, serPort, gui)
        self.echo_q = echo_q    # this is where received packets are stored for agent threads
        
    ## end __init__

    def run(self):

        ### Main Loop ###
        while self.evt_run.is_set():
            try:
                line = self.serPort.readline() # look for new lines from serial port
                self.gui.update_system_data(line) # update textrx_box with new line received
                #if line.startswith('M104'): # check if line received was a command confirmation echo
                #    self.echo_q.put(line) # if so, put line in echo_q to confirm successful cmd receipt
                    
            except (ser.SerialException, IOError), detail:
                logger.debug('Exception in TVAC_Port_Rcvr')
                break
                
            time.sleep(0.001)
            
    ## end run
## end class TVAC_Port_Rcvr
