import sys, time

sys.path.insert(0,"../../modules/xsmu")
sys.path.insert(0,"../../apps")
sys.path.insert(0,"../../apps/widgets")
sys.path.insert(0,"../../lib")

import math
import xsmu
from XSMU_Constants import *

# Set voltage source to some value
# Call function to measure current
# Loop over the measuring function
# Print out the current values

def set_DC_voltage (xsmu_driver, value):

	mode       = SOURCE_MODE_VS
	autorange  = AUTORANGE_ON
	range      = VS_RANGE_10V
	
	xsmu_driver.setSourceParameters (mode, autorange, range, values)

def measure_current():
    
    for index in range(100):
        current = CM_getReading()
        print ("The value of current is " + current + " and the time is " + time.strftime('%H:%M:%S') + '\n') 	
   
	
def main():
	
	xsmu_driver = xsmu.Driver()
	xsmu_devices = xsmu_driver.scan()
	xsmu_driver.open(xsmu_devices[0])
	
	DC_amplitude   = float(raw_input ("Enter DC Voltage (V) : "))    # V
	
	set_DC_voltage (xsmu_driver, DC_amplitude)
	measure_current()

	xsmu_driver.close()

main()
