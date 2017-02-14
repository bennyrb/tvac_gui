# LANutils.py

import socket
import os
import sys
import re
import threading
import time
import RomadsUtils as RU
#import wx

SLEEPTIME = 0.01 # sleep time between reading from socket

################################################################################

class pingIP(threading.Thread):
    def __init__(self,ip):
        threading.Thread.__init__(self)
        self.ip = ip
    def run(self):
        pingResp = os.popen( 'ping -n 1 -w 100 '+self.ip, 'r' )
        while True:
            line = pingResp.readline()
            if not line: 
                break
        time.sleep(0.001)
    
################################################################################

class portRecvr(threading.Thread):
    def __init__(self, sock, gui):
        threading.Thread.__init__(self)
        self.sock = sock
        self.connected = True
        self.gui = gui
        self.evt_run = threading.Event()
        
        self.evt_run.set()
        
    def run(self):
        print 'started portrecvr'
        HEADERSIZE = 7
        HEADERSTR = chr(0x7e)+chr(0x42)+chr(0x00)+chr(0x00)
        
        while self.evt_run.is_set():
            pktStr = readStr = ''
            headerCnt = HEADERSIZE
            remainCnt = 0
            
            # synchronize: look for first 4 header bytes
            while self.evt_run.is_set():
                try:
                    readStr = self.sock.recv(headerCnt)
                    pktStr += readStr
                    if len(pktStr) == HEADERSIZE:
                        if pktStr[:4] == HEADERSTR:
                            print 'header found:',[ord(i) for i in pktStr],
                            # get size of payload (7th byte) ...
                            remainCnt = ord(pktStr[6]) + 3	# add 3 for crc + end flag
                            break	# valid header bytes, get rest of pkt
                        else:
                            pktStr = pktStr[1:]	# shift over one char
                            headerCnt += 1
                    headerCnt -= len(readStr)
                except socket.error:
                    pass
                    #time.sleep(SLEEPTIME)
            
            while remainCnt > 0 and self.evt_run.is_set():	# loop to get entire packet
                try:
                    readStr = self.sock.recv(remainCnt)
                    pktStr += readStr	# accumulate packet
                    print 'body chunk found:',[ord(i) for i in readStr]
                    remainCnt -= len(readStr)
                except socket.error:
                    pass
                    #time.sleep(SLEEPTIME)
                            
            if self.evt_run.is_set():
                newpkt = RU.RomadsPacket(pktStr)
                print 'LAN: received from bot pkt', newpkt.msgID
                wx.CallAfter(self.gui.bot_rx_handler, newpkt)
            
        print 'exiting portRecvr'
        
    def close(self):
        self.evt_run.clear()
    
################################################################################
def getHostIP():
    """
    Get the IP address of the host.
    Return the IP address as a string.
    """
    
    localIP = socket.gethostbyname(socket.gethostname())
    return localIP


################################################################################
def getBaseIP(BaseMAC):
    """
    getBaseIP() first determines the IP address of the localhost. It then
    sends out a "ping" to all IP addresses in the entire range of the last byte, 
    i.e., X.X.X.0-255, where the X's are the same values as the localhost. 
    This creates a table of IP addresses with corresponding MAC addresses.
    The IP address of the base is determined by searching the table for an IP
    address with a MAC address that matches the base's known MAC address of 
    00-20-4a-63-bb-f8.
    
    Returns a string of the base IP address if successful; returns empty string
    otherwise.
    """
    if sys.platform != 'win32':
        print 'This function only runs on the win32 platform.'
        return ''
        
    # get local IP address
    localip = getHostIP().split('.')

    print 'Starting search for Base...\n'
    pingList = []

    hostList = range(0,256)
    if int(localip[3]) in hostList:	# check if present before removing
        hostList.remove( int(localip[3]) )	# remove localhost from ping list
    
    for host in hostList:
        ip = localip[0]+'.'+localip[1]+'.'+localip[2]+'.'+str(host)
        current = pingIP(ip)
        current.start()
        pingList.append(current)

    for pingle in pingList: pingle.join()
    
    IPstr = checkARPTable(BaseMAC)
    
    return IPstr

################################################################################

def checkBaseIP(baseIP, baseMAC):
    """
    Check if the base is at a given IP address (baseIP) by 
    sending a ping and checking the ARP table for a correct
    IP-MAC pair.
    """
        
    pingThread = pingIP(baseIP)
    pingThread.start()
    pingThread.join()
    
    if checkARPTable(baseMAC) == baseIP:
        return True
    else:
        return False

################################################################################

def checkARPTable(MAC):
    """
    Search the ARP table for a given MAC. 
    Return the corresponding IP address if the MAC is found,
    otherwise return an empty string.
    """
    
    MACRE = re.compile(r'(\S+).*'+MAC+'.*')
    arpStr = os.popen( 'arp -a', 'r')	# get table of IP - MAC addresses
    
    while True:
        line = arpStr.readline()
        if not line:
            return ''
        IPstr = re.findall( MACRE, line )
        if IPstr != []:
            print '>>>> Found Base IP Address:',IPstr[0],'<<<<\n'
            return IPstr[0]
    
################################################################################

def openSocket():
    """
    Create a socket for a TCP connection, but do not connect.
    Return the socket object if successful,
    otherwise return None.
    """
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return s
    except socket.error, detail:
        print 'Error opening socket!', detail
        return None
    
################################################################################
