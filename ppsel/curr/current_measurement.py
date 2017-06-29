import sys, time

sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import math
import xsmu
import csv
from XSMU_Constants import *

# Set voltage source to 0
# Call function to measure IV
# Print out the (voltage, current, time) values

# Change voltage source to (value + step_size)

# measure current, if (current_new - current_old) > current_step -> switch mode to current
   # Set current source to (last measured current value + current_step) 
   # Call function to measure current
   # Call function to measure voltage
   # Loop over the measuring functions
   # Print out the (voltage, current, time) values
   
# measure current, if (current_new - current_old) < current_step -> keep the new voltage value
   # Call function to measure current
   # Call function to measure voltage
   # Loop over the measuring functions
   # Print out the (voltage, current, time) values


def set_DC_voltage (xsmu_driver, value):

			#	mode       = SOURCE_MODE_VS
			#	autorange  = AUTORANGE_ON
			#	range      = VS_RANGE_10V	
			#	xsmu_driver.setSourceParameters (mode, autorange, range, value)
	xsmu_driver._VS_setVoltage(value)

def set_DC_current (xsmu_driver, value):

			#	mode       = SOURCE_MODE_CS
			#   autorange  = AUTORANGE_ON
			#	range      = VS_RANGE_10V	
			#	xsmu_driver.setSourceParameters (mode, autorange, range, value)

	xsmu_driver._CS_setCurrent(value)

def measure_IV (xsmu_driver, iteration):
    
    filename = open("histogram_data.txt", "w")
    for index in range(iteration):
        current = xsmu_driver.CM_getReading(filterLength = 1)
        voltage = xsmu_driver.VM_getReading(filterLength = 1)
        filename.write(str(voltage) + "," + str(current) + "," + str(time.strftime('%H:%M:%S')) + "\n")
    filename.close()
    
def main():
	
	xsmu_driver = xsmu.Driver()
	xsmu_devices = xsmu_driver.scan()
	xsmu_driver.open(xsmu_devices[0])
	
	DC_Voltage_Amplitude   = float(raw_input ("Enter DC Starting Voltage (V)   : "))    # V
	DC_Voltage_StepSize    = float
	iteration      = int  (raw_input ("Enter no of iterations : "))    # no of measurements
	
	set_DC_voltage (xsmu_driver, DC_amplitude)
	measure_IV     (xsmu_driver,    iteration)

	raw_input ("Press enter after observing signals")
	
	set_DC_voltage (xsmu_driver, 0.0)
	xsmu_driver.close()

main()
