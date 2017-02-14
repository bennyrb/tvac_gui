# TVACUtils.py

import TVAC_config as TC
import PyQt5.QtWidgets as pqw
import PyQt5.QtCore as pqc
import PyQt5.QtGui as pqg
import random
import numpy as np
from Queue import Queue, Empty
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import logging as lg

NO_VALUE_FOUND = '--'

class Thermo_Module(object):
    def __init__(self, module_index, setpoint_temp=TC.DEFAULT_SETPOINT_TEMP):
        # self.name_to_value_map = { \
        # 'filt_temp': [self.update_filter_temp, -1], \
        # 'inst_temp':[self.update_instant_temp, -1], \
        # 'rtd': [self.update_rtdres, 0], \
        # 'currsetpt': [self.update_curr_setpoint_temp, 0], \
        # 'pwm': [self.update_pwm, 0], \
        # 'radc': [self.update_radc, 0], \
        # 'vsense': [self.update_vsense, 0], \
        # 'isense': [self.update_isense, 0], \
        # 'rtdfails': [self.update_rtdfails, 0], \
        # 'power': [self.update_power, 0]
        # }
        
        self.module_index = module_index
        self.module_name = 'T' + str(module_index + 1)
        self.module_name_label = pqw.QLabel(self.module_name)
        self.filter_temp = -1
        self.filter_temp_array = []
        self.filter_temp_label = pqw.QLabel('---')
        self.instant_temp = -1
        self.instant_temp_array = []
        self.instant_temp_label = pqw.QLabel('---')
        self.rtdres = 0
        self.rtdres_array = []
        self.rtdres_label = pqw.QLabel('---')
        self.curr_setpoint_temp = '---'
        self.curr_setpoint_temp_array = []
        self.curr_setpoint_temp_label = pqw.QLabel(str(self.curr_setpoint_temp))
        self.pwm_val = 0
        self.pwm_val_array = []
        self.pwm_val_label = pqw.QLabel('---')
        self.radc_val = 0
        self.radc_val_array = []
        self.radc_val_label = pqw.QLabel('---')
        self.vsense = 0
        self.vsense_array = []
        self.vsense_label = pqw.QLabel('---')
        self.isense = 0
        self.isense_array = []
        self.isense_label = pqw.QLabel('---')
        self.rtdfails = 0
        self.rtdfails_array = []
        self.rtdfails_label = pqw.QLabel('---')
        self.power = 0
        self.power_label = pqw.QLabel('---')
        self.send_setpoint_temp = setpoint_temp
        self.send_setpoint_temp_textinput = SelectOnFocusLineEdit(str(self.send_setpoint_temp))
        self.send_setpoint_temp_textinput.setMaxLength(3)
        self.send_setpoint_temp_textinput.setFixedWidth(45)
        
        self.module_layout = pqw.QGridLayout()
        self.module_layout.addWidget(self.module_name_label, 0, 0, 1, 1)
        self.module_layout.addWidget(self.instant_temp_label, 1, 0, 1, 1)
        self.module_layout.addWidget(self.filter_temp_label, 2, 0, 1, 1)
        self.module_layout.addWidget(self.curr_setpoint_temp_label, 3, 0, 1, 1)
        self.module_layout.addWidget(self.send_setpoint_temp_textinput, 4, 0, 1, 1)
        
        self.module_grpbox = self.module_layout
        #self.module_grpbox = pqw.QGroupBox(self.module_name)
        #self.module_grpbox.setLayout(self.module_layout)
        
        #self.textinput.setEnabled(False) # initally disable text input
        
    def update_send_setpoint_temp(self):
        
        try:
            self.send_setpoint_temp = int(self.send_setpoint_temp_textinput.text())
        except TypeError, detail:
            pass

    ## end update_set_temp
    
    def reset_send_setpoint_temp(self, new_setpoint):
        
        self.send_setpoint_temp_textinput.setText(str(new_setpoint))
        
    ## end reset_send_setpoint_temp
    
    def update_filter_temp(self, new_filter_temp):
        try:
            self.filter_temp_label.setText(str('%0.1f' % new_filter_temp))
            self.filter_temp = new_filter_temp
        except TypeError, detail:
            self.filter_temp_label.setText(NO_VALUE_FOUND)
        # if len(self.filter_temp_array) == TC.MAX_TIME_PTS:
        #     self.filter_temp_array.pop(0)
        # self.filter_temp_array.append(new_filter_temp)
       
    ## end update_filter_temp
    
    def update_instant_temp(self, new_instant_temp):
        
        try:
            self.instant_temp_label.setText(str('%0.1f' % self.instant_temp))
            self.instant_temp = new_instant_temp
        except TypeError, detail:
            self.instant_temp_label.setText(NO_VALUE_FOUND)
        # if len(self.instant_temp_array) == TC.MAX_TIME_PTS:
        #     self.instant_temp_array.pop(0)
        # self.instant_temp_array.append(new_instant_temp)
        
    ## end update_instant_temp
    
    def update_rtdres(self, new_rtdres):
        
        try:
            self.rtdres_label.setText(str('%0.1f' % self.rtdres))
            self.rtdres = new_rtdres
        except TypeError, detail:
            self.rtdres_label.setText(NO_VALUE_FOUND)
        # if len(self.rtdres_array) == TC.MAX_TIME_PTS:
        #     self.rtdres_array.pop(0)
        # self.rtdres_array.append(new_rtdres)
        
    ## end update_rtdres
    
    def update_curr_setpoint_temp(self, new_curr_setpoint_temp):
        
        try:
            self.curr_setpoint_temp_label.setText(str('%0.1f' % new_curr_setpoint_temp))
            self.curr_setpoint_temp = new_curr_setpoint_temp
        except TypeError, detail:
            self.curr_setpoint_temp_label.setText(NO_VALUE_FOUND)
        
    ## end update_curr_setpoint_temp
    
    def update_pwm_val(self, new_pwm_val):
        
        try:
            self.pwm_val_label.setText(str('%0.1f' % new_pwm_val))
            self.pwm_val = new_pwm_val
        except TypeError, detail:
            self.pwm_val_label.setText(NO_VALUE_FOUND)
        #if len(self.pwm_val_array) == TC.MAX_TIME_PTS:
        #    self.pwm_val_array.pop(0)
        #self.pwm_val_array.append(new_pwm_val)
        
    ## end update_pwm_val
    
    def update_radc_val(self, new_radc_val):
    
        try:
            self.radc_val_label.setText(str('%0.1f' % new_radc_val))
            self.radc_val = new_radc_val
        except TypeError, detail:
            self.radc_val_label.setText(NO_VALUE_FOUND)
        # if len(self.radc_val_array) == TC.MAX_TIME_PTS:
        #     self.radc_val_array.pop(0)
        # self.radc_val_array.append(new_radc_val)
        
    ## end update_radc
    
    def update_vsense(self, new_vsense):
    
        try:
            self.vsense_label.setText(str('%0.1f' % new_vsense))
            self.vsense = new_vsense
        except TypeError, detail:
            self.vsense_label.setText(NO_VALUE_FOUND)
        
    ## end update_vsense
    
    def update_isense(self, new_isense):
    
        try:
            self.isense_label.setText(str('%0.1f' % new_isense))
            self.isense = new_isense
        except TypeError, detail:
            self.isense_label.setText(NO_VALUE_FOUND)
        
    ## end update_isense
    
    def update_rtdfails(self, new_rtdfails):
    
        try:
            self.rtdfails_label.setText(str('%0.1f' % new_rtdfails))
            self.rtdfails = new_rtdfails
        except TypeError, detail:
            self.rtdfails_label.setText(NO_VALUE_FOUND)
        
    ## end update_rtdfails
    
    def update_power(self):
        
        try:
            self.power = ((TC.HEATER_SUPPLY_VOLTAGE**2) * self.pwm) / (TC.PWM_MAX *  TC.HEATER_RESISTANCE)
            self.power_label.setText(self.power)
        except TypeError, detail:
            self.power_label.setText(NO_VALUE_FOUND)

    ## end update_power
    
    def update_values(self, newdata):
        """
        Receives dictionary that maps variable names (TC.INST_TEMP, TC.FILT_TEMP, etc.)
        to values of those variables. Then calls the update functions for those variables
        in order to save the variable values and change the displayed labels.
        """
    
        #for name in newdata.keys():
            # call the update function defined in name_to_value_map
            # with the value stored in name_to_value_map
            #self.name_to_value_map[name][0]( self.name_to_value_map[name][1] )
        
        # need to update power separately since calculated from other values: isense^2*vsupply*dutycycle
        
        try:
            self.latest_data = newdata
            self.update_instant_temp(newdata[TC.INST_TEMP])
            self.update_filter_temp(newdata[TC.FILT_TEMP])
            self.update_rtdres(newdata[TC.RTD_RESISTANCE])
            self.update_pwm_val(newdata[TC.PWM_VAL])
            self.update_curr_setpoint_temp(newdata[TC.CURR_SETPT_TEMP])
            # self.update_power()
        except KeyError, detail:
            print 'KeyError while updating values', detail
            
## end class Thermo_Module
    
class SelectOnFocusLineEdit(pqw.QLineEdit):
    def __init__(self, parent=None):
        super(SelectOnFocusLineEdit, self).__init__(parent)
        
    ## end __init__
    
    def mousePressEvent(self, evt):
        self.selectAll()
        
    ## end mousePressEvent
## end class ThermoLineEdit

class TimerLabel(pqw.QLabel):
    def __init__(self, time_text, parent=None):
        super(TimerLabel, self).__init__(parent)
        
        self.time_text = time_text
        self.setText(time_text)
        update_timer = pqc.QTimer(self)
        update_timer.timeout.connect(self.update_label)
        update_timer.start(1000)
        
    ## end __init__
    
    def update_label(self):
        self.setText(self.time_text)
        self.update()
        
    ## end update_label
    
    def set_time_text(self, newtime):
        self.time_text = newtime
            
    ## end set_time_text
    
class Plot_Canvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=8, height=5, dpi=100):
        #super(Plot_Canvas, self).__init__(parent)
        self.num_channels = TC.NUM_THERMO_MODULES
        
        #fig = Figure(figsize=(width, height), dpi=dpi)
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        #legend = plt.legend([self.axes], [label for label in label_list])
        #self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   pqw.QSizePolicy.Expanding,
                                   pqw.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        #update_timer = pqc.QTimer(self)
        #update_timer.timeout.connect(self.update_figure)
        #update_timer.start(1000)
        
        # create data array, one row for time index, one row for each channel
        self.data_array = [ [] for i in range(self.num_channels + 1) ]
        self.time_array = []

        self.max_time_pts = TC.MAX_TIME_PTS
        self.min_time_pts = TC.MIN_TIME_PTS 
        
        self.num_channels = TC.NUM_DISPLAY_CHANNELS
        
    ## end __init__

    def update_figure(self, new_x, new_y_array):
        
        # for i in range(len(newdata)):
            # self.data[i].append(newdata[i])

        # check if reached max time window (time points)
        # remove oldest data point if max data length is reached
        if len(self.time_array) == self.max_time_pts:
            self.time_array.pop(0)
            for i in range(len(self.data_array)):
                self.data_array[i].pop(0)

        self.time_array.append(new_x)
        for i in range(4): #len(new_y_array)):
            self.data_array[i].append(new_y_array[i])

        self.axes.cla()
        self.line_list = []

        for i in range(self.num_channels):
            line = self.axes.plot(self.time_array, self.data_array[i], TC.MODULE_TO_COLORCODE[i+1])
            self.line_list.append(line)
        self.draw()

    ## end update_figure

    def reset_figure(self):
        self.axes.cla()
        self.time_array = []
        self.data_array = [ [] for i in range(self.num_channels + 1) ]

    ## end reset_figure