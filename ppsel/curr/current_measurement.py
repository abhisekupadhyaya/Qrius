#------------------------------------------------------------------------------------------------
#
# ALGORITHM FOR IV MEASUREMENTS
#
# Set voltage source to 0
# Call function to measure IV
# Print out the (voltage, current, time) values
# Change voltage source to (value + step_size)
#
# measure current, if (current_new - current_old) > current_step -> switch mode to current
# 	Set current source to (last measured current value + current_step) 
# 	Call function to measure current
# 	Call function to measure voltage
# 	Loop over the measuring functions
# 	Print out the (voltage, current, time) values
#
# measure current, if (current_new - current_old) < current_step -> keep the new voltage value
# 	Call function to measure current
# 	Call function to measure voltage
# 	Loop over the measuring functions
# 	Print out the (voltage, current, time) values
#
#-------------------------------------------------------------------------------------------------

import sys, time

sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import xsmu
import csv
from XSMU_Constants import *

filename = open("histogram_data.txt", "w")
filename.close ()

def set_DC_voltage (xsmu_driver, value):

															#	mode       = SOURCE_MODE_VS
	xsmu_driver._VS_setVoltage(value)						#	autorange  = AUTORANGE_ON
															#	range      = VS_RANGE_10V	
															#	xsmu_driver.setSourceParameters (mode, autorange, range, value)

def set_DC_current (xsmu_driver, value):

															#	mode       = SOURCE_MODE_CS
															#   autorange  = AUTORANGE_ON
	xsmu_driver._CS_setCurrent(value)						#	range      = VS_RANGE_10V	
															#	xsmu_driver.setSourceParameters (mode, autorange, range, value)
	

def measure_IV (xsmu_driver, iteration):
    
    filename = open("histogram_data.txt", "a")
    
    for index in range(iteration):
        current         = xsmu_driver.CM_getReading(filterLength = 1)
        voltage         = xsmu_driver.VM_getReading(filterLength = 1)
        filename.write                             (str(voltage) + "," + str(current) + "," + str(time.strftime('%H:%M:%S')) + "\n")
        
    filename.write ('Next Source Value\n')
    filename.close ()
    
def main():
	
	xsmu_driver            = xsmu       .Driver()
	xsmu_devices           = xsmu_driver.scan  ()
	xsmu_driver.open                           (xsmu_devices[0])
	
	DC_Voltage_Amplitude   = float(raw_input ("Enter DC Voltage Max       (V)   : "))    # V
	DC_Voltage_StepSize    = float(raw_input ("Enter DC Voltage Step Size (V)   : "))    # Delta_V
	iteration              = int  (raw_input ("Enter no of iterations : "          ))    # no of measurements
	voltage                = 0.0
	
	while (voltage <= DC_Voltage_Amplitude):
		set_DC_voltage (xsmu_driver, voltage)
		measure_IV     (xsmu_driver,    iteration)
		voltage            = voltage + DC_Voltage_StepSize

	raw_input ("Press enter after observing signals")
	
	set_DC_voltage    (xsmu_driver, 0.0)
	xsmu_driver.close ()

main()
