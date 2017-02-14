# TVAC_config.py

# Example data string:
# 10453	Time in tenths of a seconds; IE 1.3s = 13, 10452 = 1045.2s or 17.42min
# Tcur1:36.89	Filtered Temperature output.  Filter type is "weighted average 95/5"
# Tnew1:36.87	Instantaneous temperature reading, no filter, no averaging.
# R1:1143.29	Instantaneous RTD reading, no filter, no averaging.
# /0.00	Temperature Setpoint in degC
# @0.00	Current PWM value
# RADC1:773	ADC value read from external current sensor
# RV1:2.49	External current sensor Voltage calculated from ADC value
# RC1:0.12	External current sensor Current calculated from Voltage Value
# FailNum1:0	# of failures detected on the MAX31865 RTD Sensor

NUM_DISPLAY_CHANNELS = 4
NUM_TOTAL_CHANNELS = 15

DEFAULT_SETPOINT_TEMP = 18 # default setpoint temperature in degrees C
INIT__SETPOINT_TEMP = DEFAULT_SETPOINT_TEMP

DEMO_MODE = False

# choose channel plot colors here
MODULE_COLORS = {1:'red', 2:'orange', 3:'green', 4:'blue', 5:'cyan', 6:'magenta', 7:'black', 8:'yellow'}
COLOR_TO_COLORCODE = {'red':'r', 'orange':'k', 'green':'g', 'blue':'b', \
                    'cyan':'k', 'magenta':'m', 'black':'k', 'yellow':'y'}
# automatically generate dictionary to map channel color to matplotlib color code 
MODULE_TO_COLORCODE = { key: COLOR_TO_COLORCODE[MODULE_COLORS[key]] for key in MODULE_COLORS.keys() }

MAX_TIME_WINDOW = 20 # maximum amount of time to display in minutes
MIN_TIME_WINDOW = 1 # minimum amount of time to display in minutes
SAMPLE_FREQ = 2
MAX_TIME_PTS = 60 * SAMPLE_FREQ * MAX_TIME_WINDOW
MIN_TIME_PTS = 60 * SAMPLE_FREQ * MIN_TIME_WINDOW

FEEDBACK_SYMBOLS = ['Tcur', 'Tnew', 'R', '/', '@', 'RADC', 'RV', 'RC', 'FailNum']
INST_TEMP = FEEDBACK_SYMBOLS[0]
FILT_TEMP = FEEDBACK_SYMBOLS[1]
RTD_RESISTANCE = FEEDBACK_SYMBOLS[2]
CURR_SETPT_TEMP = FEEDBACK_SYMBOLS[3]
PWM_VAL = FEEDBACK_SYMBOLS[4]
RADC_VAL = FEEDBACK_SYMBOLS[5]
VSENSE = FEEDBACK_SYMBOLS[6]
ISENSE = FEEDBACK_SYMBOLS[7]
RTDFAILS = FEEDBACK_SYMBOLS[8]
SYMBOL_TO_NAME_MAP = {FILT_TEMP:'filt_temp', INST_TEMP:'inst_temp', RTD_RESISTANCE:'rtd', CURR_SETPT_TEMP:'currsetpt', \
            PWM_VAL:'pwm', RADC_VAL:'radc', VSENSE:'vsense', ISENSE:'isense', RTDFAILS:'rtdfails'}

DISPLAY_VARIABLE = INST_TEMP

PWM_MAX = 255.0 # for power calculation