# Gateway.py

import sys
import logging as lg
import LANUtils as lan
import SerialUtils as SU
import serial as ser
import socket

reload(lg)
reload(lan)
reload(SU)

logger = lg.getLogger('root.GW')
logger.setLevel(lg.DEBUG)
logger.addHandler(lg.NullHandler())

class Gateway(object):
    def __init__(self, portType, gui):
        self.portType = portType
        self.gui = gui
        self.connected = False
        
        if portType == 'LAN':
            self.ip = ''
            self.TCPport = ''
            
            try:
                self.socket = lan.openSocket()	# open socket, don't connect yet
            except socket.error, detail:
                print 'Error opening socket:', detail
                return None
        
        else:
            self.baudRate = 115200
            self.port_name = 2
            self.timeout = SU.TIMEOUT
            
            # create serial port instance without opening; data format: 8N1
            self.serialPort = ser.Serial(
                                port=None,
                                baudrate=self.baudRate,
                                bytesize=ser.EIGHTBITS,
                                parity=ser.PARITY_NONE,
                                stopbits=ser.STOPBITS_ONE,
                                timeout=None,
                                xonxoff=0,
                                rtscts=0
                                )
            
    ## end __init__
        
    def connect(self, ip=None, TCPport=None, port_name='None', port_path='None'):
        if self.portType == 'LAN':
            if ip != None: self.ip = ip
            if TCPport != None: self.TCPport = TCPport
            
            try:
                self.socket.connect( (self.ip, self.TCPport) )	
                self.socket.setblocking(True)
                self.socket.settimeout(0.1)
            except socket.error, detail:
                print 'Error connecting to server %s at port %i.' % (self.ip, self.TCPport)
                print detail
                return False
            
            self.send = self.socket.send
            self.portRcvr = lan.portRecvr(self.socket, self.gui)
            self.portRcvr.start()
            self.connected = True
    
            return True
    
        else:
            # serial port
            if port_name != 'None': self.port_name = port_name
            if port_path != 'None': self.port_path = port_path
            
            try:
                self.serialPort.port = self.port_path
                self.serialPort.baudrate = self.baudRate
                self.serialPort.open()
            except (ser.SerialException, ValueError), detail:
                if sys.platform == 'win32':
                    print 'Error opening port COM%i.' % (self.port_name + 1)
                else:
                    print 'Error opening port %s.' % self.port_name
                print detail
                return False
            
            self.send = self.serialPort.write
            self.portRcvr = SU.portRecvr(self.serialPort, self.gui)
            self.portRcvr.start()
            self.serialPort.flushInput()	# flush input buffer
            self.serialPort.flushOutput()	# flush output buffer
            self.connected = True
            #self.send = self.serialPort.write
            
            return True
            
    ## end connect 
        
    def close(self):
        if self.portType == 'LAN':
            self.portRcvr.close()
            self.portRcvr.join()
            del self.portRcvr ###########################
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            del self.socket

        else:
            self.portRcvr.close()
            self.portRcvr.join()
            self.serialPort.close()
            print 'closed serial port'
        
        self.connected = False

    ## end close 
## end Gateway 

class TVAC_Gateway(Gateway):
    def __init__(self, portType, echo_q, gui):
        Gateway.__init__(self, portType, gui)
        self.port_name = 'None'
        self.port_path = 'None'
        self.echo_q = echo_q
        self.connected = False

        logger.debug('initialized TVAC gateway')

    def connect(self, new_port=None):
        if new_port != None: 
            self.port_name = new_port.port_name
            self.port_path = new_port.port_path
        
        try:
            # serial port has been created but not yet connected, 
            # so now connect using given parameters
            self.serialPort.port = self.port_path
            self.serialPort.baudrate = self.baudRate
            self.serialPort.timeout = self.timeout
            self.serialPort.open()
            logger.debug('serial port successfully opened!')
        except (ser.SerialException, ValueError), detail:
            if sys.platform.startswith('win'):
                print 'Error opening port COM%i.' % (self.port_name + 1)
            else:
                print 'Error opening port %s.' % self.port_name
            print detail
            return False
        
        self.send = self.serialPort.write # relabel function 'serialPort.write' to more convenient 'send'
        self.portRcvr = SU.TVAC_Port_Rcvr(self.serialPort, self.echo_q, self.gui)
        self.portRcvr.start()   # start receiver thread
        self.serialPort.flushInput()    # flush input buffer
        self.serialPort.flushOutput()   # flush output buffer
        self.connected = True

        return True

    def send_string(self, tx_string):
        for c in tx_string:
            try:
                self.send(c.encode()) # encode to unicode if not already
            except (ser.SerialException, ser.SerialTimeoutException, TypeError), detail:
                logger.debug('serial send failed', detail)
                
    def update_port(self, new_port):
        # new_port is a Port_Object (defined in SerialUtils) with attributes port_index, port_name and port_path
        if not self.connected:
            self.port_name = new_port.port_name
            self.port_path = new_port.port_path
            logger.debug('updated new port: %s' % self.port_name)
            return True

        else:
            print 'Port already connected. Disconnect port before updating.'
            return False

    def close(self):
        self.portRcvr.close()
        self.portRcvr.join()
        self.serialPort.close()
        self.connected = False
        logger.debug('Closed climber serial port')

