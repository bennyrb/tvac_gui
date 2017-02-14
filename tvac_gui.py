
# climber_gui.py

import sys
import os
import time
import glob
import Queue
import PyQt5.QtCore as pqc
import PyQt5.QtWidgets as pqw
import logging as lg
import serial as ser
#import cmpy.machines as cmm
import Gateway as GW
import SerialUtils as SU
import ClimberSystemUtils as CSU
import ClimberConfig as CC
import ClimberAgent as CA
import ClimberSystemThread as CST
import TVAC_config as TC
import TVACUtils as TU
import math

# force a reload of modules in case they were changed from last run
reload(lg)
reload(GW)
reload(SU)
reload(CSU)
reload(CC)
reload(CA)
reload(CST)
reload(TC)
reload(TU)

# configure logging
logger = lg.getLogger()
logger.setLevel(lg.DEBUG)

logch = lg.StreamHandler()
logch.setLevel(lg.DEBUG)

logformatter = lg.Formatter('[%(name)s] %(message)s')

logch.setFormatter(logformatter)

logger.addHandler(logch)
## done configure logging

class Form(pqw.QWidget):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        self.speed = 0
        self.motor_enabled = False
        self.fluxpkt_id = 0
        self.climbpkt_id = 0
        self.fcmd_pkt = CSU.Fluxor_Command_Packet()
        self.ccmd_pkt = CSU.Climber_Command_Packet()
        self.packet_q = Queue.Queue()
        self.flux_pkt_q = Queue.Queue()
        self.climb_pkt_q = Queue.Queue()
        
        self.echo_q = Queue.Queue() # queue to receive cmd echoes from board
        
        self.init_comms() # must initialize communications before initializing layout
        self.init_layout()

        self.getpkt_count = 0

    ## end __init__

    def init_comms(self):
        # create a Climber_Gateway object to be used as a communications port
        self.comm_port = GW.TVAC_Gateway("serial", self.echo_q, self)

    ## end init_comms

    def init_layout(self):
        logger.debug('init layout')
        comm_panel = self.init_comm_panel()
        single_cmd_panel = self.init_single_cmd_panel()
        group_cmd_panel = self.init_group_cmd_panel()
        data_panel = self.init_data_panel()
        logfile_panel = self.init_logfile_panel()
        
        main_layout = pqw.QGridLayout()
        main_layout.addWidget(comm_panel, 0, 0, 1, 1)
        main_layout.addWidget(single_cmd_panel, 0, 1, 1, 1)
        main_layout.addWidget(logfile_panel, 0, 2, 1, 3)
        main_layout.addWidget(group_cmd_panel, 1, 0, 1, 5)
        main_layout.addWidget(data_panel, 2, 0, 3, 5)
        #main_layout.addWidget(step_panel, 4, 0, 2, 4)
        
        self.setLayout(main_layout)
        self.setWindowTitle("TVAC Controller")
        
        if TC.DEMO_MODE:
            update_timer = pqc.QTimer(self)
            self.timeval = 0
            #self.testfile = open('logfile_20170202183239.txt')
            self.enable_data_logging(True)
            update_timer.timeout.connect(self.update_test)
            update_timer.start(1000)

    ## end init_layout

    def init_comm_panel(self):
        self.connect_label = pqw.QLabel('Not Connected')
        self.connect_label.setFixedWidth(90)
        self.rescan_ports_button = pqw.QPushButton('Rescan Ports')
        self.connect_button = pqw.QPushButton('Connect')

        # port_combobox is a pull-down menu of available ports. It is a QComboBox with a
        # Port_Object (defined in SerialUtils) as its data. A Port_Object has attributes
        # port_index, port_name and port_path
        self.port_combobox = pqw.QComboBox()

        # generate list of available serial ports 
        self.port_list = self.get_serial_port_list() 
        # populate combobox menu with list of available serial ports
        for (p_index, p_object) in self.port_list.viewitems():
            self.port_combobox.addItem(p_object.port_name, p_object)
        # set combobox to first element in list of ports
        self.port_combobox.setCurrentText(self.port_list[0].port_name)
        # set comm_port to be same as what is displayed in port_combobox
        self.comm_port.update_port(self.port_combobox.currentData())

        if self.comm_port.port_name == 'None':
            self.port_combobox.setEnabled(False)
            self.connect_button.setEnabled(False)
        else:
            self.port_combobox.setEnabled(True)
            self.connect_button.setEnabled(True)

        # connect buttons to handlers
        self.connect_button.clicked.connect(self.connect_toggle)
        self.rescan_ports_button.clicked.connect(self.update_serialport_menu)

        # create layout
        comm_layout = pqw.QGridLayout()
        comm_layout.addWidget(self.port_combobox, 0, 0, 1, 2)
        comm_layout.addWidget(self.rescan_ports_button, 0, 2, 1, 1)
        comm_layout.addWidget(self.connect_label, 1, 0, 1, 2)
        comm_layout.addWidget(self.connect_button, 1, 2, 1, 1)
        comm_grpbox = pqw.QGroupBox('Communications')
        comm_grpbox.setLayout(comm_layout)

        return comm_grpbox

    ## end init_comm_panel

    def update_serialport_menu(self):
        # generate list of available serial ports 
        self.port_list = self.get_serial_port_list() 
        # clear combobox of any old items
        self.port_combobox.clear()
        logger.debug('cleared serial port pull-down menu')

        # populate combobox menu with list of available serial ports
        for (p_index, p_object) in self.port_list.viewitems():
            self.port_combobox.addItem(p_object.port_name, p_object)

        # set combobox to first element in list of ports
        self.port_combobox.setCurrentText(self.port_list[0].port_name)

        # set comm_port to be same as displayed in port_combobox
        self.comm_port.update_port(self.port_combobox.currentData())

        if self.comm_port.port_name == 'None':
            self.port_combobox.setEnabled(False)
            self.connect_button.setEnabled(False)
        else:
            self.port_combobox.setEnabled(True)
            self.connect_button.setEnabled(True)

    ## end rescan_serial_ports

    def init_single_cmd_panel(self):
        logger.debug('creating single cmd panel')
        ser_str_slabel = pqw.QLabel('Command string to send')
        self.ser_str_textinput = pqw.QLineEdit()
        self.send_ser_str_button = pqw.QPushButton('Send Cmd String')
        last_cmd_slabel = pqw.QLabel('Last Cmd Sent:')
        self.sent_cmd_dlabel = pqw.QLabel('None')
        cmd_stat_slabel = pqw.QLabel('Cmd Status:')
        self.stat_dlabel = pqw.QLabel('None')
        
        self.ser_str_textinput.setEnabled(False) # initially disable text input
        self.send_ser_str_button.setEnabled(False) # initially disable button
        self.send_ser_str_button.clicked.connect(self.send_single_cmd) # bind button & method

        single_cmd_layout = pqw.QGridLayout()
        single_cmd_layout.addWidget(ser_str_slabel, 0, 0, 1, 1)
        single_cmd_layout.addWidget(self.ser_str_textinput, 1, 0, 1, 3)
        single_cmd_layout.addWidget(self.send_ser_str_button, 2, 0, 1, 3)
        single_cmd_layout.addWidget(last_cmd_slabel, 3, 0, 1, 1)
        single_cmd_layout.addWidget(self.sent_cmd_dlabel, 3, 1, 1, 1)
        single_cmd_layout.addWidget(cmd_stat_slabel, 4, 0, 1, 1)
        single_cmd_layout.addWidget(self.stat_dlabel, 4, 1, 1, 1)
        
        single_cmd_grpbox = pqw.QGroupBox('Single Command')
        single_cmd_grpbox.setLayout(single_cmd_layout)

        return single_cmd_grpbox

    ## end init_serial_panel

    def init_group_cmd_panel(self):
        module_label = pqw.QLabel('Thermo Module')
        module_label.setMaximumWidth(100)
        module_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        instant_temp_label = pqw.QLabel('Instantaneous Temp\n(deg C)')
        instant_temp_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        filter_temp_label = pqw.QLabel('Filtered Temp\n(deg C)')
        filter_temp_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        curr_setpoint_temp_label = pqw.QLabel('Current Setpoint Temp\n(deg C)')
        curr_setpoint_temp_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        send_setpoint_temp_label = pqw.QLabel('Send Setpoint Temp\n(deg C)')
        send_setpoint_temp_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        
        group_cmd_layout = pqw.QGridLayout()
        group_cmd_layout.addWidget(module_label, 0, 0, 1, 1)
        group_cmd_layout.addWidget(instant_temp_label, 1, 0, 1, 1)
        group_cmd_layout.addWidget(filter_temp_label, 2, 0, 1, 1)
        group_cmd_layout.addWidget(curr_setpoint_temp_label, 3, 0, 1, 1)
        group_cmd_layout.addWidget(send_setpoint_temp_label, 4, 0, 1, 1)
        
        self.tmod_array = []
        
        for i in range(TC.NUM_DISPLAY_CHANNELS):
            self.tmod_array.append(TU.Thermo_Module(i))
            group_cmd_layout.addWidget(self.tmod_array[i].module_name_label, 0, i+1, 1, 1)
            group_cmd_layout.addWidget(self.tmod_array[i].instant_temp_label, 1, i+1, 1, 1)
            group_cmd_layout.addWidget(self.tmod_array[i].filter_temp_label, 2, i+1, 1, 1)
            group_cmd_layout.addWidget(self.tmod_array[i].curr_setpoint_temp_label, 3, i+1, 1, 1)
            group_cmd_layout.addWidget(self.tmod_array[i].send_setpoint_temp_textinput, 4, i+1, 1, 1)
        
        self.send_grp_cmd_button = pqw.QPushButton('Send Group Command')
        self.send_grp_cmd_button.setEnabled(False)
        self.send_grp_cmd_button.clicked.connect(self.send_group_cmd)

        self.reset_tfields_button = pqw.QPushButton('Reset Setpoints')
        self.reset_tfields_button.setEnabled(False)
        self.reset_tfields_button.clicked.connect(self.reset_tfields)
        
        group_cmd_layout.addWidget(self.reset_tfields_button, 5, 0, 1, 1)
        group_cmd_layout.addWidget(self.send_grp_cmd_button, 5, 1, 1, TC.NUM_DISPLAY_CHANNELS)
        
        group_cmd_grpbox = pqw.QGroupBox('Group Command')
        group_cmd_grpbox.setLayout(group_cmd_layout)
        
        return group_cmd_grpbox
        
    ## end init_group_cmd_panel
    
    def init_data_panel(self):
        lastdata_label = pqw.QLabel('Time of last data received:')
        lastdata_label.setAlignment(pqc.Qt.AlignRight | pqc.Qt.AlignVCenter)
        
        self.lastdata_time_label = TU.TimerLabel('--')
        self.lastdata_time_label.setFixedWidth(300)
        
        clear_textrx_button = pqw.QPushButton('Clear Data Received Box')
        clear_textrx_button.clicked.connect(self.clear_textrx)
        
        self.textrx_box = pqw.QTextEdit()
        self.textrx_box.setMinimumWidth(800)
        self.textrx_box.setMinimumHeight(200)
        self.textrx_box.setLineWrapMode(pqw.QTextEdit.NoWrap)
        self.textrx_box.setReadOnly(True)
        
        textrx_layout = pqw.QGridLayout()
        textrx_layout.addWidget(clear_textrx_button, 0, 0, 1, 1)
        textrx_layout.addWidget(self.textrx_box, 1, 0, 1, 4)
        textrx_tab = pqw.QWidget()
        textrx_tab.setLayout(textrx_layout)
        
        self.data_plot = TU.Plot_Canvas() # canvas for realtime data plotting
        self.data_plot.setMinimumWidth(800)
        self.data_plot.setMinimumHeight(200)
        
        dataplot_layout = pqw.QGridLayout()
        dataplot_layout.addWidget(self.data_plot, 0, 0)
        dataplot_tab = pqw.QWidget()
        dataplot_tab.setLayout(dataplot_layout)

        data_tabs_panel = pqw.QTabWidget()
        data_tabs_panel.addTab(dataplot_tab, 'Data Plot')
        data_tabs_panel.addTab(textrx_tab, 'Serial Text Received')

        data_panel_layout = pqw.QGridLayout()
        data_panel_layout.addWidget(lastdata_label, 0, 0, 1, 1)
        data_panel_layout.addWidget(self.lastdata_time_label, 0, 1, 1, 3)
        data_panel_layout.addWidget(data_tabs_panel, 1, 0, 4, 4)
        data_panel_grpbox = pqw.QGroupBox('Data Received')
        data_panel_grpbox.setLayout(data_panel_layout)
        
        return data_panel_grpbox
        
    ## end init_textrx_panel
    
    def clear_textrx(self):
        self.textrx_box.clear()
        
    ## end clear_textrx
    
    def update_system_data(self, line_raw):
        self.textrx_box.append(line_raw) # add new line to text received box, remove extra '\n'
        self.lastdata_time_label.set_time_text(time.asctime())
        
        line_parsed = self.parse_line(line_raw) # parse data from line received
        if line_parsed != None:
            self.write_datafiles(line_raw, line_parsed) # write raw and parsed data to separate files
            self.update_tmod_display(line_parsed) # update GUI thermo module data fields
            self.update_plot(line_parsed[0], TC.DISPLAY_VARIABLE)
        else:
            logger.debug('line could not be parsed')
            print line_raw
    ## end update_system_data
    
    def write_datafiles(self, line_raw, line_parsed):

        try:
            self.logfileraw.write(line_raw) # write to log file
            
        except (ValueError, AttributeError), detail:
            logger.debug("error writing to raw logfile")
            print 'system update raw logfile error:', detail
            
        try:
            datastr = str(line_parsed[0]) + ' ' # first save time index
            # now get data from each channel
            for i in range(1, TC.NUM_TOTAL_CHANNELS + 1):
                for sym in TC.FEEDBACK_SYMBOLS:
                    if sym != '/' and sym != '@':
                        sym_num = sym + str(i)
                    else:
                        sym_num = sym
                    datastr += str(line_parsed[i][sym_num]) + ' '

            self.logfileparsed.write(datastr + '\n') # write to log file
            
        except (ValueError, AttributeError), detail:
            logger.debug("error writing to parsed logfile")
            print 'system update parsed logfile error:', detail

    ## end write_datafiles

    def update_tmod_display(self, line_parsed):

        # line_parsed is a list that holds a time index in element 0, followed by one 
        # dictionary for each possible channel. The keys of the dictionaries are the 
        # symbols defined in FEEDBACK_SYMBOLS in TVAC_config.py, concatenated with 
        # the channel number, and their values are numerical variable values 
        # (not strings of variable values).

        # iterate through the thermo modules being displayed
        for i in range(len(self.tmod_array)):
            # Because there may be some symbols such as '/' and '@' that do not have channel
            # numbers appended to them, we cannot blanketly add or remove channel numbers to 
            # the keys of the dictionary. Instead, we must re-create the dictionary with 
            # the appropriate keys that can be properly interpreted by the Thermo_Module object.
            symbol_data = {}
            for sym in TC.FEEDBACK_SYMBOLS:
                if sym != '/' and sym != '@':
                    sym_num = sym + str(i+1)
                else:
                    sym_num = sym
                symbol_data[sym] = line_parsed[i+1][sym_num] # use i+1 since i=0 is time index
            # now we can update tmod_array with the appropriate dictionary
            self.tmod_array[i].update_values(symbol_data) 
            
    def update_plot(self, newtimeval, display_var):
        newdatavals = [ self.tmod_array[i].latest_data[display_var] for i in range(TC.NUM_DISPLAY_CHANNELS) ]
        self.data_plot.update_figure(newtimeval, newdatavals)

    ## end update_plot

    def update_test(self):
        self.timeval += 1
        print 'timeval=', self.timeval
        sindata = [ math.sin(self.timeval*0.1), math.sin((self.timeval+1)*0.1), math.sin((self.timeval+2)*0.1), math.sin((self.timeval+3)*0.1)]
        self.data_plot.update_figure(self.timeval, sindata)
        line = '%d : %s:%d %s:%d %s:%d %s:%d' % (self.timeval, 'Tnew1', sindata[0], 'Tnew2', sindata[1], 'Tnew3', sindata[2], 'Tnew4', sindata[3])
        #line = self.testfile.readline()
        self.update_system_data(line)

    def parse_line(self, line):
        if line.startswith('M104'):
            return None
            
        complete_data = [] # all data parsed from line

        # first look for time index before getting data
        line = line.strip() # remove all leading & trailing spaces
        endpos = line.find(' ') # look for space after time index

        try:
            timeindex = int(line[:endpos]) # try converting to int
            complete_data.append(timeindex) # save timeindex as first element

        except ValueError, detail:
            logger.debug('ValueError: unexpected start of line, error converting timeindex to int')
            return None

        # now go through rest of line to parse data
        for i in range(TC.NUM_TOTAL_CHANNELS):
            symbol_data = {} # data parsed for one channel

            # go through expected symbols in list defined in config file
            for sym in TC.FEEDBACK_SYMBOLS:
                if sym != '/' and sym != '@':
                    sym_num = sym + str(i+1) # create string to look for, e.g., "Tnew1"
                else:
                    sym_num = sym
                startpos = line.find(sym_num)###
                
                # if sym not found, record '--' for that symbol and skip to next symbol
                if startpos == -1:
                    symbol_data[sym_num] = '--'
                    continue
                
                # now that we've found the symbol we're looking for, extract the numerical data
                line = line[startpos:] # remove previously scanned data from line
                
                if sym_num != '/' and sym_num != '@': # check if regular numbered symbol or special unnumbered symbol
                    startpos = len(sym_num) + 1 # get start position of data number; should be char right after ':'
                    #if line[:sym_end] == sym_num:
                    #line = line[startpos:] # remove chars before number
                    #line = line.strip() # remove any extra leading/trailing spaces
                    #else: # log unexpected symbol in data stream and continue
                    #    print 'unexpected symbol found in data stream', line[:line.find(':')+1]
                    #    continue
                else:
                    if sym_num == '/':
                        startpos = line.find('/') + 1 # number should be immediately after symbol
                    elif sym_num == '@':
                        startpos = line.find('@') + 1
                    #line = line[startpos:]
                    #line = line.strip()
                line = line[startpos:] # remove chars before number
                line = line.strip() # remove any extra leading/trailing spaces

                # now the beginning of the line should be the start of the number and we just look for a space
                # to mark the end of the number
                endpos = line.find(' ') # look for first space after number
                numstr = line[:endpos] # number should be between these positions
                
                try:
                    # first check if string is int
                    if numstr.isdigit():
                        num = int(numstr) 
                    # else try converting to float
                    else:
                        num = float(numstr) 

                    #if sym in TC.SYMBOL_TO_NAME_MAP.keys():
                    #    symbol_data[ TC.SYMBOL_TO_NAME_MAP[sym] ] = num # save new number to variable name
                    
                except ValueError, detail:
                    print 'ValueError, string not convertible to number', numstr
                    print detail
                
                symbol_data[sym_num] = num # save number to variable name
            
            #self.tmod_array[i].update_values( symbol_data )
            complete_data.append(symbol_data)
        
        return complete_data
                
    ## end parse_line
    
    def send_single_cmd(self):
        raw_string = self.ser_str_textinput.text()
        if raw_string[-1] != '\n':
            raw_string += '\n'
            #print 'raw_string needs newline'
        
        print 'sending string... ', raw_string
        self.sendcmd_waitecho(raw_string)
        
    ## end send_single_cmd

    def send_group_cmd(self):
        for tmod in self.tmod_array:
            tmod.update_send_setpoint_temp()
            ser_str = self.prep_ser_str(tmod.module_index, tmod.send_setpoint_temp)
            self.sendcmd_waitecho(ser_str)
            
    ## end send_serial_group
    
    def prep_ser_str(self, tmod_num, tmod_setpoint):
        ser_str = 'M104' + str('%02i ' % (tmod_num+1)) + str('S%03i\n' % tmod_setpoint)
        return ser_str
        
    ## end prep_ser_str
    
    def sendcmd_waitecho(self, cmdstr, timeout=0.05):
        """
        Send a command, then continuously look for an echo until a timeout is reached. Upon successful command 
        execution, the board returns the same command string sent.
        """
        try:
                
            self.comm_port.send_string(cmdstr)
            logger.debug( cmdstr )
            #self.print_hex(cmdstr)

        except:
            self.open_error_dialog()
            print 'error sending string!'
            return

        newstr = None
        timestart = time.time()
        
        # look for echo in timeout loop
        while time.time() - timestart < timeout:
            try:
                newstr = self.echo_q.get_nowait()
                print 'got new str:', len(newstr), newstr
                print 'old str:', len(newstr), cmdstr
                
                if newstr == cmdstr:
                    print 'Correct echo received:', newstr
                    logger.debug('successful packet, time elapsed=%f' % time.time()-timestart)
            except Queue.Empty:
                time.sleep(0.01)
            
    ## end wait_fluxor_stat
    
    def reset_tfields(self):
        for tmod in self.tmod_array:
            tmod.reset_send_setpoint_temp(TC.DEFAULT_SETPOINT_TEMP)
        
    ## end reset_tfields
    
    def init_logfile_panel(self):
        self.logfileraw_name = self.generate_logfilename('_raw.txt')
        logfileraw_label = pqw.QLabel('Raw Data File Name')
        self.logfileraw_name_textinput = TU.SelectOnFocusLineEdit(self.logfileraw_name)
        self.logfileraw_name_textinput.setMaxLength(128)
        logfileraw_layout = pqw.QGridLayout()
        logfileraw_layout.addWidget(self.logfileraw_name_textinput)
        logfileraw_grpbox = pqw.QGroupBox('Raw Data File Name')
        logfileraw_grpbox.setLayout(logfileraw_layout)
        
        self.logfileparsed_name = self.generate_logfilename('_parsed.txt')
        logfileparsed_label = pqw.QLabel('Parsed Data File Name')
        self.logfileparsed_name_textinput = TU.SelectOnFocusLineEdit(self.logfileparsed_name)
        self.logfileparsed_name_textinput.setMaxLength(128)
        logfileparsed_layout = pqw.QGridLayout()
        logfileparsed_layout.addWidget(self.logfileparsed_name_textinput)
        logfileparsed_grpbox = pqw.QGroupBox('Parsed Data File Name')
        logfileparsed_grpbox.setLayout(logfileparsed_layout)
        
        self.logfilename_button = pqw.QPushButton('Generate New File Name')
        self.logfilename_button.clicked.connect(self.update_logfilename)
        
        logfile_layout = pqw.QGridLayout()
        #logfile_layout.addWidget(logfileraw_label, 0, 0, 1, 1)
        #logfile_layout.addWidget(self.logfileraw_name_textinput, 0, 1, 1, 3)
        logfile_layout.addWidget(logfileraw_grpbox, 0, 0, 1, 4)
        #logfile_layout.addWidget(logfileparsed_label, 1, 0, 1, 1)
        #logfile_layout.addWidget(self.logfileparsed_name_textinput, 1, 1, 1, 3)
        logfile_layout.addWidget(logfileparsed_grpbox, 1, 0, 1, 4)
        logfile_layout.addWidget(self.logfilename_button, 2, 0, 1, 4)
        
        logfile_grpbox = pqw.QGroupBox('Log File')
        logfile_grpbox.setLayout(logfile_layout)
        
        return logfile_grpbox
        
    ## end init_logfile_panel
    
    def update_logfilename(self):
        self.logfileraw_name = self.generate_logfilename('_raw.txt')
        self.logfileraw_name_textinput.setText(self.logfileraw_name)
        self.logfileparsed_name = self.generate_logfilename('_parsed.txt')
        self.logfileparsed_name_textinput.setText(self.logfileparsed_name)
        
    ## end update_logfilename
    
    def generate_logfilename(self, extension):
        currtime = time.localtime()
        logfilename = 'logfile_' + str(currtime.tm_year) + ('%02i'% currtime.tm_mon) + \
        ('%02i'% currtime.tm_mday) + ('%02i'% currtime.tm_hour) + \
        ('%02i'% currtime.tm_min) + ('%02i'% currtime.tm_sec) + extension
        
        return logfilename
        
    ## end generate_logfilename
    
    def enable_data_logging(self, enable_log):
        if enable_log:
            self.logfileraw = open(self.logfileraw_name, 'a')
            self.logfileparsed = open(self.logfileparsed_name, 'a')
            logger.debug('opened logfiles')
            self.logfileraw_name_textinput.setEnabled(False)
            self.logfileparsed_name_textinput.setEnabled(False)
            self.logfilename_button.setEnabled(False)
            
        else:
            self.logfileraw.close()
            self.logfileparsed.close()
            logger.debug('closed logfiles')
            self.logfileraw_name_textinput.setEnabled(True)
            self.logfileparsed_name_textinput.setEnabled(True)
            self.logfilename_button.setEnabled(True)
            
    ## end enable_data_logging
    
    def enable_cmd_panels(self):
        self.ser_str_textinput.setEnabled(True)
        self.send_ser_str_button.setEnabled(True)
        self.reset_tfields_button.setEnabled(True)
        self.send_grp_cmd_button.setEnabled(True)
        
    ## end enable_cmd_panels
    
    def disable_cmd_panels(self):
        self.ser_str_textinput.setEnabled(False)
        self.send_ser_str_button.setEnabled(False)
        self.reset_tfields_button.setEnabled(False)
        self.send_grp_cmd_button.setEnabled(False)
    
    ## end disable_cmd_panels
    
    def connect_toggle(self):
        if self.comm_port.connected:
            # currently connected, now disconnect
            self.disable_cmd_panels()
            self.comm_controls_disconnected()
            
            self.enable_data_logging(False)
            self.comm_port.close() # finally close the port
            logger.debug('disconnected from port')
            self.connect_button.setText('Connect')
            self.connect_label.setText('Not Connected')
            
        else: 
            # currently disconnected, now try to connect
            if self.comm_port.connect(self.port_combobox.currentData()): 
                # successful connection
                self.enable_data_logging(True)
                self.comm_controls_connected()
                self.enable_cmd_panels()
                self.connect_button.setText('Disconnect')
                self.connect_label.setText('Connected')
                logger.debug('successully connected to port')
                
            else:
                # connection error
                self.signal_error('Error connecting to port.')

    ## end connect_toggle

    def get_serial_port_list(self):
        # PortList is a dictionary with an index number as the key and a Port_Object as the value
        # A Port_Object (defined in SerialUtils) has attributes index, name and path
        PortList = {}
        # check if any serial port devices found
        if sys.platform.startswith('win'):
            allports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            allports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            allports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
		
        ports = []
		
        for port in allports:
            try:
                s = ser.Serial(port)
                s.close()
                ports.append(port)
            except (OSError, ser.SerialException):
                pass
                
        if len(ports) == 0:
            nullport = SU.NULL_PORT()
            PortList[nullport.port_index] = nullport
            print 'No serial ports found.'
        else:
            for n,p in enumerate(ports):
				#if sys.platform.startswith('win'):
				PortList[ n ] = SU.Port_Object(n, p, p)
				#else:
				#	PortList[ n ] = SU.Port_Object(n, p, p)

        return PortList

    ## end get_serial_port_list

    def comm_controls_disconnected(self):
        self.rescan_ports_button.setEnabled(True)
        self.port_combobox.setEnabled(True)

    ## end comm_controls_disconnected

    def comm_controls_connected(self):
        self.rescan_ports_button.setEnabled(False)
        self.port_combobox.setEnabled(False)

    ## end comm_controls_connected

    def signal_error(self, error_message):
        print error_message
    ## end signal_error

    def closeEvent(self, event):
        if self.comm_port.connected:
            # currently conencted, now disconnect before quitting app
            self.connect_toggle() # this will disable the motor, then close the port
            logger.debug('Quitting and closing port...')
        else:
            logger.debug('Quitting, no ports to close.')
    ## end closeEvent

    def open_error_dialog(self):
        pass
    ## end open_error_dialog

if __name__ == '__main__':
    app = pqw.QApplication(sys.argv)
    screen = Form()
    screen.show()
    sys.exit(app.exec_())
